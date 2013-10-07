#!/usr/bin/env python

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
        self.text = Tkinter.Text()
        self.text.pack()
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
        timestring = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        dirname = 'decrypted_'+timestring+'/'
        if not os.path.isdir(dirname):
            os.mkdir(dirname)
        fin = tkFileDialog.askopenfilenames()
        for f in fin:
            try:
                self.decrypt_file(f, dirname+os.path.basename(f)+'_decrypted')
            except:
                self.sane_insert("Error decrypting: "+f)
        self.sane_insert('Wrote decrypted files to '+dirname)
    def batch_encrypt(self, recipient=None):
        recipient = self.get_recipient()
        if recipient is None:
            self.sane_insert("You must specify an email address for encryption")
            return
        timestring = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        dirname = 'encrypted_'+timestring+'/'
        if not os.path.isdir(dirname):
            os.mkdir(dirname)
        fin = tkFileDialog.askopenfilenames()
        for f in fin:
            try:
                self.encrypt_file(f, dirname+os.path.basename(f)+'_encrypted', recipient)
            except:
                self.sane_insert("Error encrypting: "+f)
        self.sane_insert('Wrote encrypted files to '+dirname)
    def encrypt_file(self, input_file, output_file, recipient):
        args = [GPG, '--output', output_file, '--recipient', recipient, '-sea', input_file]
        subprocess.call(args)
    def decrypt_file(self, input_file, output_file):
        args = [GPG, '--output', output_file, '--decrypt', input_file]
        subprocess.call(args)
    def do_exit(self):
        root.destroy()


root = Tkinter.Tk()
root.title("a simple GnuPG interface")
app = GpgApp(root)
root.mainloop()
