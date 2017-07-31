# -*- coding: utf-8 -*-
"""Testing utilities related to setup and teardown of test environment.
"""
import os
from os.path import abspath, dirname, exists, isdir, join, realpath
import shutil
import subprocess

import gnupg

os.environ['SECUREDROP_ENV'] = 'test'
import config
import crypto_util
from db import init_db, db_session

FILES_DIR = abspath(join(dirname(realpath(__file__)), '..', 'files'))

# TODO: the PID file for the redis worker is hard-coded below.  Ideally this
# constant would be provided by a test harness.  It has been intentionally
# omitted from `config.py.example` in order to isolate the test vars from prod
# vars.  When refactoring the test suite, the test_worker_pidfile
# test_worker_pidfile is also hard-coded in `manage.py`.
TEST_WORKER_PIDFILE = "/tmp/securedrop_test_worker.pid"


def create_directories():
    """Create directories for the file store and the GPG keyring.
    """
    for d in (config.SECUREDROP_DATA_ROOT, config.STORE_DIR,
              config.GPG_KEY_DIR, config.TEMP_DIR):
        if not isdir(d):
            os.mkdir(d)


def init_gpg():
    """Initialize the GPG keyring and import the journalist key for
    testing.
    """
    gpg = gnupg.GPG(homedir=config.GPG_KEY_DIR)
    # Faster to import a pre-generated key than to gen a new one every time.
    for keyfile in (join(FILES_DIR, "test_journalist_key.pub"),
                    join(FILES_DIR, "test_journalist_key.sec")):
        gpg.import_keys(open(keyfile).read())
    return gpg


def setup():
    """Set up the file system, GPG, and database."""
    create_directories()
    init_gpg()
    init_db()
    # Do tests that should always run on app startup
    crypto_util.do_runtime_tests()
    # Start the Python-RQ worker if it's not already running
    if not exists(TEST_WORKER_PIDFILE):
        subprocess.Popen(["rqworker",
                          "-P", config.SECUREDROP_ROOT,
                          "--pid", TEST_WORKER_PIDFILE])


def teardown():
    db_session.remove()
    try:
        shutil.rmtree(config.SECUREDROP_DATA_ROOT)
    except OSError as exc:
        if 'No such file or directory' not in exc:
            raise
