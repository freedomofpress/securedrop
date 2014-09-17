#!/usr/bin/env python

import sys
import os
import shutil
import subprocess
import unittest

# We need to import config in each function because we're running the tests
# directly, so it's important to set the environment correctly, depending on
# development or testing, before importing config.
#
# TODO: do we need to store *_PIDFILE in the application config? It seems like
# an implementation detail that is specifc to this management script.

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
    from tests import test_unit, test_journalist, test_single_star

    test_suites = [test_unit, test_journalist, test_single_star]

    for test_suite in test_suites:
        test_loader = unittest.defaultTestLoader.loadTestsFromModule(test_suite)
        test_runner = unittest.TextTestRunner(verbosity=2)
        test_runner.run(test_loader)

    # TODO run functional tests directly from this script
    # Until then, we're still calling the old test.sh script just to run the functional tests.
    subprocess.call(["./test.sh"])


def reset():
    """
    Clears the Securedrop development application's state, restoring it to the
    way it was immediately after running `setup_dev.sh`. This command:
    1. Erases the development sqlite database file ($SECUREDROP_ROOT/db.sqlite)
    2. Regenerates the database
    3. Erases stored submissions and replies from $SECUREDROP_ROOT/store
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

def main():
    valid_cmds = ["start", "stop", "test", "reset"]
    help_str = "./manage.py {{{0}}}".format(','.join(valid_cmds))

    if len(sys.argv) != 2 or sys.argv[1] not in valid_cmds:
        print help_str
        sys.exit(1)

    cmd = sys.argv[1]

    getattr(sys.modules[__name__], cmd)()


if __name__ == "__main__":
    main()
