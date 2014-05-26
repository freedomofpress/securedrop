#!/usr/bin/env python

import sys
import os
import shutil

import config
import db

def start():
    pass

def test():
    pass

def reset():
    """
    Clears the Securedrop development application's state, restoring it to the
    way it was immediately after running `setup_dev.sh`. This command:
    1. Erases the development sqlite database file ($SECUREDROP_ROOT/db.sqlite)
    2. Regenerates the database
    3. Erases stored submissions and replies from $SECUREDROP_ROOT/store
    """
    # Erase the development db file
    assert hasattr(config, 'DATABASE_FILE'), "TODO: ./manage.py doesn't know how to clear the db if the backend is not sqlite"
    os.remove(config.DATABASE_FILE)

    # Regenerate the database
    db.init_db()

    # Clear submission/reply storage
    for source_dir in os.listdir(config.STORE_DIR):
        # Each entry in STORE_DIR is a directory corresponding to a source
        shutil.rmtree(os.path.join(config.STORE_DIR, source_dir))

def main():
    valid_cmds = ["start", "test", "reset"]
    help_str = "./manage.py {{{0}}}".format(','.join(valid_cmds))

    if len(sys.argv) != 2 or sys.argv[1] not in valid_cmds:
        print help_str
        sys.exit(1)

    cmd = sys.argv[1]
    getattr(sys.modules[__name__], cmd)()

if __name__ == "__main__":
    main()
