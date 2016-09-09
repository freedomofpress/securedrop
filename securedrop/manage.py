#!/usr/bin/env python

import sys
import os
import shutil
import subprocess
from subprocess import CalledProcessError
import unittest
import readline  # makes the add_admin prompt kick ass
import signal
from time import sleep
import version
import qrcode
import psutil
import config

from getpass import getpass
from argparse import ArgumentParser
from db import db_session, Journalist

from babel.messages import frontend as babel
from babel.messages.extract import DEFAULT_KEYWORDS as BABEL_DEFAULT_KEYWORDS
from distutils.dist import Distribution
from management import run

# We need to import config in each function because we're running the tests
# directly, so it's important to set the environment correctly, depending on
# development or testing, before importing config.
os.environ['SECUREDROP_ENV'] = 'dev'

# TODO: the PID file for the redis worker is hard-coded below.
# Ideally this constant would be provided by a test harness.
# It has been intentionally omitted from `config.py.example`
# in order to isolate the test vars from prod vars.
# When refactoring the test suite, the TEST_WORKER_PIDFILE
# TEST_WORKER_PIDFILE is also hard-coded in `tests/common.py`.
TEST_WORKER_PIDFILE = "/tmp/securedrop_test_worker.pid"

BABEL_TRANSLATIONS_DIR = './translations'
BABEL_MESSAGES_FILE = './translations/messages.pot'


def get_pid_from_pidfile(pid_file_name):
    with open(pid_file_name) as fp:
        return int(fp.read())


def _start_test_rqworker(config):
    # needed to determine the directory to run the worker in
    worker_running = False
    try:
        if psutil.pid_exists(get_pid_from_pidfile(TEST_WORKER_PIDFILE)):
            worker_running = True
    except IOError:
        pass

    if not worker_running:
        tmp_logfile = open("/tmp/test_rqworker.log", "w")
        subprocess.Popen(
            [
                "rqworker", "test",
                "-P", config.SECUREDROP_ROOT,
                "--pid", TEST_WORKER_PIDFILE,
            ],
            stdout=tmp_logfile,
            stderr=subprocess.STDOUT)


def _stop_test_rqworker():
    os.kill(get_pid_from_pidfile(TEST_WORKER_PIDFILE), signal.SIGTERM)


def test():
    """
    Runs the test suite
    """
    os.environ['SECUREDROP_ENV'] = 'test'
    import config
    _start_test_rqworker(config)
    test_cmds = [["py.test", "--cov"], "./test.sh"]
    test_rc = int(any([subprocess.call(cmd) for cmd in test_cmds]))
    _stop_test_rqworker()
    sys.exit(test_rc)


def test_unit():
    """
    Runs the unit tests.
    """
    os.environ['SECUREDROP_ENV'] = 'test'
    import config
    _start_test_rqworker(config)
    test_rc = int(subprocess.call(["py.test", "--cov"]))
    _stop_test_rqworker()
    sys.exit(test_rc)


def reset():
    """
    Clears the SecureDrop development application's state, restoring it to the
    way it was immediately after running `setup_dev.sh`. This command:
    1. Erases the development sqlite database file
    2. Regenerates the database
    3. Erases stored submissions and replies from the store dir
    """
    import config
    import db

    # Erase the development db file
    assert hasattr(
        config, 'DATABASE_FILE'), "TODO: ./manage.py doesn't know how to clear the db if the backend is not sqlite"
    os.remove(config.DATABASE_FILE)

    # Regenerate the database
    db.init_db()

    # Clear submission/reply storage
    for source_dir in os.listdir(config.STORE_DIR):
        # Each entry in STORE_DIR is a directory corresponding to a source
        shutil.rmtree(os.path.join(config.STORE_DIR, source_dir))


def add_admin():
    while True:
        username = raw_input("Username: ")
        if Journalist.query.filter_by(username=username).first():
            print "Sorry, that username is already in use."
        else:
            break

    while True:
        password = getpass("Password: ")

        if len(password) > Journalist.MAX_PASSWORD_LEN:
            print ("Your password is too long (maximum length {} characters). "
                   "Please pick a shorter password.".format(
                   Journalist.MAX_PASSWORD_LEN))
            continue

        password_again = getpass("Confirm Password: ")

        if password == password_again:
            break
        print "Passwords didn't match!"

    hotp_input = raw_input("Is this admin using a YubiKey [HOTP]? (y/N): ")
    otp_secret = None
    if hotp_input.lower() == "y" or hotp_input.lower() == "yes":
        while True:
            otp_secret = raw_input(
                "Please configure your YubiKey and enter the secret: ")
            if otp_secret:
                break

    try:
        admin = Journalist(username=username,
                           password=password,
                           is_admin=True,
                           otp_secret=otp_secret)
        db_session.add(admin)
        db_session.commit()
    except Exception as e:
        if "username is not unique" in str(e):
            print "ERROR: That username is already taken!"
        else:
            print "ERROR: An unexpected error occurred, traceback: \n{}".format(e)
    else:
        print "Admin '{}' successfully added".format(username)
        if not otp_secret:
            # Print the QR code for Google Authenticator
            print
            print "Scan the QR code below with Google Authenticator:"
            print
            uri = admin.totp.provisioning_uri(
                username,
                issuer_name="SecureDrop")
            qr = qrcode.QRCode()
            qr.add_data(uri)
            qr.print_ascii(tty=sys.stdout.isatty())
            print
            print "If the barcode does not render correctly, try changing your terminal's font, (Monospace for Linux, Menlo for OS X)."
            print "If you are using iTerm on Mac OS X, you will need to change the \"Non-ASCII Font\", which is your profile's Text settings."
            print
            print "Can't scan the barcode? Enter following shared secret manually:"
            print admin.formatted_otp_secret
            print


def clean_tmp():
    """Cleanup the SecureDrop temp directory. This is intended to be run as an
    automated cron job. We skip files that are currently in use to avoid
    deleting files that are currently being downloaded."""
    # Inspired by http://stackoverflow.com/a/11115521/1093000
    import config

    def file_in_use(fname):
        in_use = False

        for proc in psutil.process_iter():
            try:
                open_files = proc.open_files()
                in_use = in_use or any([open_file.path == fname
                                        for open_file in open_files])
                # Early return for perf
                if in_use:
                    break
            except psutil.NoSuchProcess:
                # This catches a race condition where a process ends before we
                # can examine its files. Ignore this - if the process ended, it
                # can't be using fname, so this won't cause an error.
                pass

        return in_use

    def listdir_fullpath(d):
        # Thanks to http://stackoverflow.com/a/120948/1093000
        return [os.path.join(d, f) for f in os.listdir(d)]

    for path in listdir_fullpath(config.TEMP_DIR):
        if not file_in_use(path):
            os.remove(path)


def translate():
    cmds = [
        [
            'pybabel', 'extract',
            '--charset=utf-8',
            '--mapping=./babel.cfg',
            '--output=' + BABEL_MESSAGES_FILE,
            '--project=SecureDrop',
            "--version=\\'{}\\'".format(version.__version__),
            "--msgid-bugs-address=\\'securedrop@freedom.press\\'",
            "--copyright-holder=\\'Freedom of the Press Foundation\\'",
            '--no-wrap',
            '.',
            'source_templates',
            'journalist_templates',
        ],
        # delete this line because it blocks translation extraction and compilation
        [
            'sed',
            '-i',
            '/^#, fuzzy$/d',
            BABEL_MESSAGES_FILE,
        ],
    ]

    for locale in getattr(config, 'LOCALES', []):
        if locale.startswith('en'):
            continue

        cmd = [
            'pybabel', 'compile',
            '--locale=' + locale,
            '--input-file=./translations/{locale}/LC_MESSAGES/messages.po'.format(locale=locale),
            '--directory=' + BABEL_TRANSLATIONS_DIR,
            '--statistics',
        ]
        cmds.append(cmd)


    cmd = [
        'pybabel', 'update',
        '--input-file=' + BABEL_MESSAGES_FILE,
        '--output-dir=' + BABEL_TRANSLATIONS_DIR,
        '--no-fuzzy-matching',
        '--no-wrap',
        '--ignore-obsolete',
    ]
    cmds.append(cmd)


    for cmd in cmds:
        run_cmd(cmd)


def run_cmd(cmd):
    print('Running command:')
    print(' '.join(cmd))
    try:
        subprocess.check_output(cmd)
    except CalledProcessError as e:
        print '[ERROR] Subprocess had non-zero exit code: ' + str(e.returncode)
        print e.message
        print e.output
        sys.exit(e.returncode)


def get_args():
    parser = ArgumentParser(prog=__file__,
                            description='A tool to help admins manage and devs hack')

    subparsers = parser.add_subparsers()

    run_subparser = subparsers.add_parser('run', help='Run the dev webserver (source & journalist)')
    run_subparser.set_defaults(func=run)

    unit_test_subparser = subparsers.add_parser('unit-test', help='Run the unit tests')
    unit_test_subparser.set_defaults(func=test_unit)

    test_subparser = subparsers.add_parser('test', help='Run the full test suite')
    test_subparser.set_defaults(func=test)

    reset_subparser = subparsers.add_parser('reset', help="DANGER!!! Clears the SecureDrop application's state")
    reset_subparser.set_defaults(func=reset)

    add_admin_subparser = subparsers.add_parser('add-admin', help='Add a new admin to the application')
    add_admin_subparser.set_defaults(func=add_admin)

    clean_tmp_subparser = subparsers.add_parser('clean-tmp', help='Cleanup the SecureDrop temp directory')
    clean_tmp_subparser.set_defaults(func=clean_tmp)

    translate_subparser = subparsers.add_parser('translate', help='Update and compile translations')
    translate_subparser.set_defaults(func=translate)

    return parser


if __name__ == "__main__":  # pragma: no cover
    try:
        args = get_args().parse_args()
        # calling like this works because all functions take zero arguments
        args.func()
    except KeyboardInterrupt:
        print  # So our prompt appears on a nice new line
        exit(1)
