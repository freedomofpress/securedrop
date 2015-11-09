#!/usr/bin/env python

import sys
import subprocess
import os

SECUREDROP_DIR = "securedrop"
BABEL_FILE = "babel.cfg"
TRANSLATIONS_DIR = SECUREDROP_DIR + "/translations"
POT_FILE = TRANSLATIONS_DIR + "/messages.pot"

def init():
    """Initializes a new language"""
    if len(sys.argv) != 3:
        print "./lang_tools.py init LANG"
        sys.exit(1)
    lang = sys.argv[2]
    rc = int(subprocess.call(
        ['pybabel', 'init', '-i', POT_FILE, '-d', TRANSLATIONS_DIR, '-l', lang]))
    sys.exit(rc)

def update():
    """Extracts messages and updates PO files"""
    print "Extracting messages..."
    rc = int(subprocess.call(
        ['pybabel', 'extract', '--project=SecureDrop', '-F', BABEL_FILE, '-o', POT_FILE, SECUREDROP_DIR]))
    if rc != 0:
        sys.exit(rc)
    print "Updating PO files..."
    rc = int(subprocess.call(
        ['pybabel', 'update', '-i', POT_FILE, '-d', TRANSLATIONS_DIR]))
    sys.exit(rc)

def compile():
    """Compiles the PO files into MO files"""
    rc = int(subprocess.call(
        ['pybabel', 'compile', '-d', TRANSLATIONS_DIR]))
    sys.exit(rc)

def main():
    valid_cmds = ["init", "update", "compile"]
    help_str = "./lang_tools.py {{{0}}}".format(','.join(valid_cmds))

    if len(sys.argv) < 2 or len(sys.argv) > 3 or sys.argv[1] not in valid_cmds:
        print help_str
        sys.exit(1)

    cmd = sys.argv[1]

    wd = os.path.dirname(os.path.abspath(__file__))
    os.chdir(wd)

    try:
        getattr(sys.modules[__name__], cmd)()
    except KeyboardInterrupt:
        print # So our prompt appears on a nice new line

if __name__ == "__main__":
    main()
