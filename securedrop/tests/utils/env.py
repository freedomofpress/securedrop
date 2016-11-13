# -*- coding: utf-8 -*-
"""Testing utilities related to setup and teardown of test environment.
"""
import os
import shutil
import subprocess

import gnupg

# Set environment variable so config.py uses a test environment
os.environ['SECUREDROP_ENV'] = 'test'
import config
import crypto_util
from db import init_db

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
        if not os.path.isdir(d):
            os.mkdir(d)


def init_gpg():
    """Initialize the GPG keyring and import the journalist key for
    testing.
    """
    gpg = gnupg.GPG(homedir=config.GPG_KEY_DIR)
    # Faster to import a pre-generated key than to gen a new one every time.
    for keyfile in ("test_journalist_key.pub", "test_journalist_key.sec"):
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
    if not os.path.exists(TEST_WORKER_PIDFILE):
        subprocess.Popen(["rqworker",
                          "-P", config.SECUREDROP_ROOT,
                          "--pid", TEST_WORKER_PIDFILE])


def teardown():
    shutil.rmtree(config.SECUREDROP_DATA_ROOT)
