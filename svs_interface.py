#!/usr/bin/env python


"""
A simple GPG2 interface to batch encrypt/decrypt files.
"""

# TODO:
# * Get the user passphrase in a prompt instead of making them type it in the
# terminal
# * Make output messages more helpful
# * Functionality for one-click secure wipes


import subprocess
import Tkinter
import tkFileDialog
import tkSimpleDialog
import os
import datetime

GPG = 'gpg2'
SERVER_KEY = ''  # replace with gpg key ID of server key
DECRYPTED_PREFIX = 'decrypted'

class GpgApp(object):
    def __init__(self, master):
        frame = Tkinter.Frame(master)
        frame.pack()
        scrollbar = Tkinter.Scrollbar(master)
        scrollbar.pack(side=Tkinter.RIGHT, fill=Tkinter.Y)
        self.text = Tkinter.Text(master, yscrollcommand=scrollbar.set)
        self.text.pack()
        scrollbar.config(command=self.text.yview)
        self.sane_insert('Welcome to the decryption and encryption interface!\n')
        self.sane_insert('To encrypt and decrypt files, go to the File menu.')
        self.sane_insert('Please remember to check the Terminal window for passphrase prompts.\n')
        menu = Tkinter.Menu(master)
        root.config(menu=menu)

        filemenu = Tkinter.Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Decrypt files", command=self.batch_decrypt)
        filemenu.add_command(label="Encrypt files", command=self.batch_encrypt)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.do_exit)
    def sane_insert(self, text):
        """Insert text sanely into the UI notification box"""
        self.text.config(state=Tkinter.NORMAL)
        self.text.insert(Tkinter.END, text+'\n')
        self.text.config(state=Tkinter.DISABLED)
    def filename_open(self):
        fin = tkFileDialog.askopenfilenames()
        if fin:
            self.sane_insert(fin)
            return fin
    def get_recipient(self):
        prompt = "Enter the email address to encrypt files to: "
        recipient = tkSimpleDialog.askstring("Encrypt files", prompt)
        return recipient
    def batch_decrypt(self):
        fin = tkFileDialog.askopenfilenames()
        if not fin:
            return
        dirname = self.get_timestamped_folder('decrypted')
        for f in fin:
            self.decrypt_file(f, dirname+os.path.basename(f)+'_decrypted')
        self.sane_insert('Wrote decrypted files to '+dirname)
    def batch_encrypt(self, recipient=None):
        recipient = self.get_recipient()
        if recipient is None:
            self.sane_insert("You must specify an email address for encryption")
            return
        fin = tkFileDialog.askopenfilenames()
        if not fin:
            return
        dirname = self.get_timestamped_folder('encrypted')
        for f in fin:
            self.encrypt_file(f, dirname+os.path.basename(f)+'_encrypted', recipient)
        self.sane_insert('Wrote encrypted files to '+dirname)
    def encrypt_file(self, input_file, output_file, recipient):
        args = [GPG, '--output', output_file, '--recipient', recipient, '-sea', input_file]
        self.do_subprocess(args)
    def decrypt_file(self, input_file, output_file):
        args = [GPG, '--output', output_file, '--decrypt', input_file]
        self.do_subprocess(args)
    def get_timestamped_folder(self, prefix):
        timestring = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        dirname = prefix+'_'+timestring+'/'
        if not os.path.isdir(dirname):
            os.mkdir(dirname)
        return dirname
    def do_subprocess(self, cmd):
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         stdin=subprocess.PIPE)
        out, err = proc.communicate()
        if err: self.sane_insert(err)
    def do_exit(self):
        root.destroy()


root = Tkinter.Tk()
root.title("a simple GnuPG interface")
app = GpgApp(root)
root.mainloop()
