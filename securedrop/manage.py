#!/usr/bin/env python

import atexit
import sys
import os
import select
import shutil
import subprocess
import unittest
import readline  # makes the add_admin prompt kick ass
from getpass import getpass
import signal
from time import sleep

import qrcode
import psutil

from db import db_session, Journalist

# We need to import config in each function because we're running the tests
# directly, so it's important to set the environment correctly, depending on
# development or testing, before importing config.
#
# TODO: do we need to store *_PIDFILE in the application config? It seems like
# an implementation detail that is specifc to this management script.

os.environ['SECUREDROP_ENV'] = 'dev'

WORKER_PIDFILE = "/tmp/test_rqworker.pid"


def get_pid_from_pidfile(pid_file_name):
    with open(pid_file_name) as fp:
        return int(fp.read())


def _start_test_rqworker(config):
    # needed to determine the directory to run the worker in
    worker_running = False
    try:
        if psutil.pid_exists(get_pid_from_pidfile(WORKER_PIDFILE)):
            worker_running = True
    except IOError:
        pass

    if not worker_running:
        tmp_logfile = open("/tmp/test_rqworker.log", "w")
        subprocess.Popen(
            [
                "rqworker", "test",
                "-P", config.SECUREDROP_ROOT,
                "--pid", WORKER_PIDFILE,
            ],
            stdout=tmp_logfile,
            stderr=subprocess.STDOUT)


def _stop_test_rqworker():
    os.kill(get_pid_from_pidfile(WORKER_PIDFILE), signal.SIGTERM)


def run():
    """
    Starts development servers for both the Source Interface and the
    Document Interface concurrently. Their output is collected,
    labeled, and sent to stdout to present a unified view to the
    developer.

    Ctrl-C will kill the servers and return you to the terminal.

    Useful resources:
    * https://stackoverflow.com/questions/22565606/python-asynhronously-print-stdout-from-multiple-subprocesses

    """

    def colorize(s, color, bold=False):
        # https://www.siafoo.net/snippet/88
        shell_colors = {
            'gray': '30',
            'red': '31',
            'green': '32',
            'yellow': '33',
            'blue': '34',
            'magenta': '35',
            'cyan': '36',
            'white': '37',
            'crimson': '38',
            'highlighted_red': '41',
            'highlighted_green': '42',
            'highlighted_brown': '43',
            'highlighted_blue': '44',
            'highlighted_magenta': '45',
            'highlighted_cyan': '46',
            'highlighted_gray': '47',
            'highlighted_crimson': '48'
        }

        # http://stackoverflow.com/a/2330297/1093000
        attrs = []
        attrs.append(shell_colors[color])
        if bold:
            attrs.append('1')

        return '\x1b[{}m{}\x1b[0m'.format(';'.join(attrs), s)


    class DevServerProcess(subprocess.Popen):

        def __init__(self, label, cmd, color):
            self.label = label
            self.cmd = cmd
            self.color = color

            super(DevServerProcess, self).__init__(
                self.cmd,
                stdin  = subprocess.PIPE,
                stdout = subprocess.PIPE,
                stderr = subprocess.STDOUT,
                preexec_fn = os.setsid)

        def print_label(self, to):
            label = "\n => {} <= \n\n".format(self.label)
            if to.isatty():
                label = colorize(label, self.color, True)
            to.write(label)


    class DevServerProcessMonitor(object):

        def __init__(self, procs):
            self.procs = procs
            self.streams = [proc.stdout for proc in procs]
            self.last_proc = None
            atexit.register(self.cleanup)

        def _get_proc_by_stream(self, stream):
            # TODO: this could be optimized, but it hardly matters when there
            # are only two processes being monitored.
            for proc in self.procs:
                if id(stream) == id(proc.stdout):
                    return proc

        def monitor(self):
            while True:
                # TODO: we currently don't handle input, which makes using an
                # interactive debugger like pdb impossible. Since Flask provides
                # a featureful in-browser debugger, I'll accept that pdb is
                # broken for now. If someone really wants it, they should be
                # able to change this function to make it work (although I'm not
                # sure how hard it would be).
                #
                # If you really want to use pdb, you can just run the
                # application scripts individually (`python source.py` or
                # `python journalist.py`).
                rstreams, _, _ = select.select(self.streams, [], [])

                for stream in rstreams:
                    current_proc = self._get_proc_by_stream(stream)
                    # To keep track of which process output what, print a
                    # helpful label every time the process sending output
                    # changes.
                    if current_proc != self.last_proc:
                        current_proc.print_label(sys.stdout)
                        self.last_proc = current_proc

                    line = stream.readline()
                    sys.stdout.write(line)
                    sys.stdout.flush()

                if any(proc.poll() is not None for proc in self.procs):
                    # If any of the processes terminates (for example, due to
                    # a syntax error causing a reload to fail), kill them all
                    # so we don't get stuck.
                    sys.stdout.write(colorize(
                        "\nOne of the development servers exited unexpectedly. "
                        "See the traceback above for details.\n"
                        "Once you have resolved the issue, you can re-run "
                        "'./manage.py run' to continue developing.\n\n",
                        "red", True))
                    self.cleanup()
                    break

            for proc in self.procs:
                proc.wait()

        def cleanup(self):
            for proc in self.procs:
                if proc.poll() is None:
                    # When the development servers use automatic reloading, they
                    # spawn new subprocess frequently. In order to make sure we
                    # kill all of the subprocesses, we need to send SIGTERM to
                    # the process group and not just the process we initially
                    # created. See http://stackoverflow.com/a/4791612/1093000
                    os.killpg(proc.pid, signal.SIGTERM)
                    proc.terminate()

    procs = [
        DevServerProcess('Source Interface',
                         ['python', 'source.py'],
                         'blue'),
        DevServerProcess('Document Interface',
                         ['python', 'journalist.py'],
                         'cyan'),
    ]

    monitor = DevServerProcessMonitor(procs)
    monitor.monitor()

def test():
    """
    Runs the test suite
    """
    os.environ['SECUREDROP_ENV'] = 'test'
    import config
    _start_test_rqworker(config)
    test_cmds = ["py.test", "./test.sh"]
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
    test_rc = int(subprocess.call("py.test"))
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

    admin = Journalist(
        username=username,
        password=password,
        is_admin=True,
        otp_secret=otp_secret)
    try:
        db_session.add(admin)
        db_session.commit()
    except Exception as e:
        if "username is not unique" in str(e):
            print "ERROR: That username is already taken!"
        else:
            print "ERROR: An unknown error occurred, traceback:"
            print e
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
            print "Can't scan the barcode? Enter the shared secret manually: {}".format(admin.formatted_otp_secret)
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


def main():
    valid_cmds = [
        "run",
        "test_unit",
        "test",
        "reset",
        "add_admin",
        "clean_tmp"]
    help_str = "./manage.py {{{0}}}".format(','.join(valid_cmds))

    if len(sys.argv) != 2 or sys.argv[1] not in valid_cmds:
        print help_str
        sys.exit(1)

    cmd = sys.argv[1]

    try:
        getattr(sys.modules[__name__], cmd)()
    except KeyboardInterrupt:
        print  # So our prompt appears on a nice new line


if __name__ == "__main__":
    main()
