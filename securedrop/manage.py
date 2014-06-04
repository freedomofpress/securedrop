#!/usr/bin/env python

import sys
import os
import shutil
import subprocess
import signal
import psutil

os.environ['SECUREDROP_ENV'] = 'development'


def start():
    for proc in psutil.process_iter():
        for command in  proc.cmdline:
            if 'source' in command:
                print "killing: " + str(command)
                proc.kill()
            if 'journalist' in command:
                print "killing: " + str(command)
                proc.kill()

    subprocess.Popen(['python', 'source.py'])
    subprocess.Popen(['python', 'journalist.py'])
    print "The web application is running, and available on your Vagrant host at the following addresses:"
    print "Source interface:     localhost:8080"
    print "Journalist interface: localhost:8081"



def kill(filename):
    if os.path.isfile(filename):
        f = open(filename, 'r')
        pid = f.read()
        if pid:
            print "killing " + pid
            os.kill(int(pid), signal.SIGTERM)


def test():
    """
    Runs the test suite
    """
    # TODO: we could implement test.sh's functionality here, and get rid of
    # test.sh (now it's just clutter, and confusing)
    subprocess.call(["./test.sh"])


def reset():
    """
    Clears the Securedrop development application's state, restoring it to the
    way it was immediately after running `setup_dev.sh`. This command:
    1. Erases the development sqlite database file ($SECUREDROP_ROOT/db.sqlite)
    2. Regenerates the database
    3. Erases stored submissions and replies from $SECUREDROP_ROOT/store
    """
    # HACK: import here so they don't interfere with the test setup
    # (environment variable hasn't been set yet)
    import config
    import db

    # Erase the development db file
    assert hasattr(config,
                   'DATABASE_FILE'), "TODO: ./manage.py doesn't know how to clear the db if the backend is not sqlite"
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
