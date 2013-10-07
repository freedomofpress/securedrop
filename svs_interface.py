#!/usr/bin/env python

import subprocess
from Tkinter import *
from tkFileDialog import *
import os

GPG = 'gpg2'
SERVER_KEY = ''  # replace with gpg key ID of server key

class GpgApp(object):
    def __init__(self, master):
        frame = Frame(master)
        frame.pack()
        self.text = Text()
        self.text.pack()
        menu = Menu(master)
        root.config(menu=menu)

        filemenu = Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Open", command=self.filename_open)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.do_exit)
    def filename_open(self):
        fin = askopenfilenames()
        if fin:
            self.text.insert(END,fin)
            return fin
    def encrypt_file(self, input_file, output_file, recipient):
        args = [GPG, '--output', output_file, '--recipient', recipient, '-sea', input_file]
        subprocess.call(args)
    def do_exit(self):
        root.destroy()


root = Tk()
root.title("a simple GnuPG interface")
app = GpgApp(root)
root.mainloop()


