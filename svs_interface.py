#!/usr/bin/env python


"""
A simple GPG2 interface to batch encrypt/decrypt files.
"""

# TODO:
# * Show interactive GPG prompts in popup windows instead of making user type in the
# terminal. Might involve some subprocess pipe trickery.
# * Make output messages more helpful
# * Functionality for one-click secure wipes
# * Make the UI less ugly

import subprocess
import os
import datetime
import pygtk
pygtk.require('2.0')
import gtk

GPG = 'gpg2'
SERVER_KEY = ''  # replace with gpg key ID of server key, eventually
DECRYPT_BUTTON_TEXT = 'Decrypt files'
ENCRYPT_BUTTON_TEXT = 'Encrypt files'

class GpgApp(object):

    def __init__(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.exit)
        self.vbox = gtk.VBox()
        self.vbox.pack_start(self.init_text())
        self.hbox = gtk.HBox()
        self.init_buttons()
        self.vbox.pack_start(self.hbox)
        self.window.add(self.vbox)
        self.window.show_all()

    def delete_event(self, widget, event, data=None):
        return False

    def init_text(self):
        start_text = """Welcome to the GPG interface!\n
                        Click on the buttons below to encrypt and decrypt files.\n
                        You can select multiple files at once.\n"""
        textbox = gtk.TextView()
        text = gtk.TextBuffer()
        text.set_text(start_text)
        textbox.set_buffer(text)
        return textbox

    def init_buttons(self):
        self.encrypt_button = gtk.Button(ENCRYPT_BUTTON_TEXT)
        self.encrypt_button.connect("clicked", self.batch_encrypt)
        self.decrypt_button = gtk.Button(DECRYPT_BUTTON_TEXT)
        self.decrypt_button.connect("clicked", self.batch_decrypt)
        self.hbox.pack_start(self.decrypt_button)
        self.hbox.pack_start(self.encrypt_button)

    def notify_popup(self, message, level=gtk.MESSAGE_INFO):
        d = gtk.MessageDialog(type=level, buttons=gtk.BUTTONS_CLOSE)
        gtk.text = message
        d.run()
        d.destroy()

    def get_entry(self, prompt, visible=True):
        label = gtk.Label(prompt)
        d = gtk.Dialog(title="Input needed", buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        d.vbox.pack_start(label)
        e = gtk.Entry()
        e.set_visibility(visible)
        d.vbox.pack_start(e)
        d.show_all()
        response = d.run()
        answer = e.get_text()
        d.destroy()
        if response == gtk.RESPONSE_REJECT:
            answer = None
        return answer

    def get_recipient(self):
        prompt = "Enter the email address to encrypt files to: "
        recipient = self.get_entry(prompt)
        return recipient

    def get_files(self):
        chooser = gtk.FileChooserDialog(title="Select files",
                                        action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                                 gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        chooser.set_default_response(gtk.RESPONSE_OK)
        chooser.set_select_multiple(True)
        f = gtk.FileFilter()
        f.set_name("All files")
        f.add_pattern("*")
        chooser.add_filter(f)
        f = gtk.FileFilter()
        f.set_name(".gpg files")
        filters = [(".gpg files", "*.gpg"),
                   (".asc files",  "*.asc")]
        for name, pattern in filters:
            f = gtk.FileFilter()
            f.set_name(name)
            f.add_pattern(pattern)
            chooser.add_filter(f)
        response = chooser.run()
        fn = chooser.get_filenames()
        chooser.destroy()
        if response == gtk.RESPONSE_CANCEL:
            fn = None
        return fn

    def batch_decrypt(self, widget, data=None):
        fin = self.get_files()
        if not fin:
            return
        dirname = self.get_timestamped_folder('decrypted')
        for f in fin:
            self.decrypt_file(f, dirname+os.path.basename(f)+'_decrypted')
        self.notify_popup('Wrote decrypted files to '+dirname)

    def batch_encrypt(self, widget, data=None):
        recipient = self.get_recipient()
        if recipient is None:
            self.notify_popup("You must specify an email address for encryption")
            return
        fin = self.get_files()
        if not fin:
            return
        dirname = self.get_timestamped_folder('encrypted')
        for f in fin:
            self.encrypt_file(f, dirname+os.path.basename(f)+'_encrypted', recipient)
        self.notify_popup('Wrote encrypted files to '+dirname)

    def encrypt_file(self, input_file, output_file, recipient):
        args = [GPG, '--output', output_file, '--recipient', recipient, '-sea', input_file]
        self.do_subprocess(args)

    def decrypt_file(self, input_file, output_file):
        args = [GPG, '--output', output_file, '--decrypt', input_file]
        self.do_subprocess(args)

    def get_timestamped_folder(self, prefix):
        """Create a timestamped folder for encrypted/decrypted files"""
        timestring = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        dirname = prefix+'_'+timestring+'/'
        if not os.path.isdir(dirname):
            os.mkdir(dirname)
        return dirname

    def do_subprocess(self, cmd):
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         stdin=subprocess.PIPE)
        out, err = proc.communicate()
        if err: self.notify_popup(err, level=gtk.MESSAGE_ERROR)

    def exit(self, widget, data=None):
        """Close the window and quit"""
        gtk.main_quit()

    def main(self):
        gtk.main()

if __name__ == "__main__":
    app = GpgApp()
    app.main()
