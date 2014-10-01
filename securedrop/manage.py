#!/usr/bin/env python

import sys
import os
import shutil
import subprocess
import unittest
import readline # makes the add_admin prompt kick ass
from getpass import getpass

import qrcode

from db import db_session, Journalist

# We need to import config in each function because we're running the tests
# directly, so it's important to set the environment correctly, depending on
# development or testing, before importing config.
#
# TODO: do we need to store *_PIDFILE in the application config? It seems like
# an implementation detail that is specifc to this management script.

os.environ['SECUREDROP_ENV'] = 'dev'

def start():
    import config
    source_rc = subprocess.call(['start-stop-daemon', '--start', '-b', '--quiet', '--pidfile',
                                 config.SOURCE_PIDFILE, '--startas', '/bin/bash', '--', '-c', 'cd /vagrant/securedrop && python source.py'])
    journo_rc = subprocess.call(['start-stop-daemon', '--start', '-b', '--quiet', '--pidfile',
                                 config.JOURNALIST_PIDFILE, '--startas', '/bin/bash', '--', '-c', 'cd /vagrant/securedrop && python journalist.py'])
    if source_rc + journo_rc == 0:
        print "The web application is running, and available on your Vagrant host at the following addresses:"
        print "Source interface:     localhost:8080"
        print "Journalist interface: localhost:8081"
    else:
        print "The web application is already running.  Please use './manage.py stop' to stop."


def stop():
    import config
    source_rc = subprocess.call(
        ['start-stop-daemon', '--stop', '--quiet', '--pidfile', config.SOURCE_PIDFILE])
    journo_rc = subprocess.call(
        ['start-stop-daemon', '--stop', '--quiet', '--pidfile', config.JOURNALIST_PIDFILE])
    if source_rc + journo_rc == 0:
        print "The web application has been stopped."
    else:
        print "There was a problem stopping the web application."


def test():
    """
    Runs the test suite
    """
    os.environ['SECUREDROP_ENV'] = 'test'
    test_cmds = ["py.test", "./test.sh"]
    sys.exit(int(any([subprocess.call(cmd) for cmd in test_cmds])))

def test_unit():
    """
    Runs the unit tests.
    """
    os.environ['SECUREDROP_ENV'] = 'test'
    sys.exit(int(subprocess.call("py.test")))


def reset():
    """
    Clears the Securedrop development application's state, restoring it to the
    way it was immediately after running `setup_dev.sh`. This command:
    1. Erases the development sqlite database file
    2. Regenerates the database
    3. Erases stored submissions and replies from the store dir
    """
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


def add_admin():
    username = raw_input("Username: ")
    while True:
        password = getpass("Password: ")
        password_again = getpass("Confirm Password: ")
        if password == password_again:
            break
        print "Passwords didn't match!"

    hotp_input = raw_input("Is this admin using a Yubikey [HOTP]? (y/N): ")
    otp_secret = None
    if hotp_input.lower() == "y" or hotp_input.lower() == "yes":
        while True:
            otp_secret = raw_input("Please configure your Yubikey and enter the secret: ")
            if otp_secret:
                break

    admin = Journalist(username=username, password=password, is_admin=True, otp_secret=otp_secret)
    try:
        db_session.add(admin)
        db_session.commit()
    except Exception, e:
        if "username is not unique" in str(e):
            print "ERROR: That username is already taken!"
        else:
            print "ERROR: An unknown error occurred, traceback:"
            print e
    else:
        print "Admin {} successfully added".format(username)
        if not otp_secret:
            # Print the QR code for Google Authenticator
            print
            print "Scan the QR code below with Google Authenticator:"
            print
            uri = admin.totp.provisioning_uri(username)
            qr = qrcode.QRCode()
            qr.add_data(uri)
            qr.print_ascii(tty=sys.stdout.isatty())
            print
            print "Can't scan the barcode? Enter the shared secret manually: {}".format(admin.formatted_otp_secret)



def main():
    valid_cmds = ["start", "stop", "test_unit", "test", "reset", "add_admin"]
    help_str = "./manage.py {{{0}}}".format(','.join(valid_cmds))

    if len(sys.argv) != 2 or sys.argv[1] not in valid_cmds:
        print help_str
        sys.exit(1)

    cmd = sys.argv[1]

    try:
        getattr(sys.modules[__name__], cmd)()
    except KeyboardInterrupt:
        print # So our prompt appears on a nice new line

if __name__ == "__main__":
    main()
