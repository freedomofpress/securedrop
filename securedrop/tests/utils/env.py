# -*- coding: utf-8 -*-
"""Testing utilities related to setup and teardown of test environment.
"""
import gnupg
import os
import io
import shutil
import threading

from os.path import abspath, dirname, isdir, join, realpath

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
from sdconfig import config

from db import db

FILES_DIR = abspath(join(dirname(realpath(__file__)), '..', 'files'))

# The PID file for the redis worker is hard-coded below.  Ideally this
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
        if isdir(d):
            shutil.rmtree(d)
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
        gpg.import_keys(io.open(keyfile).read())
    return gpg


def setup():
    """Set up the file system, GPG, and database."""
    create_directories()
    init_gpg()
    db.create_all()


def teardown():
    # make sure threads launched by tests complete before
    # teardown, otherwise they may fail because resources
    # they need disappear
    for t in threading.enumerate():
        if t.is_alive() and not isinstance(t, threading._MainThread):
            t.join()
    db.session.remove()
    shutil.rmtree(config.TEMP_DIR)
    try:
        shutil.rmtree(config.SECUREDROP_DATA_ROOT)
        # safeguard for #844
        assert not os.path.exists(config.SECUREDROP_DATA_ROOT)
    except OSError as exc:
        if 'No such file or directory' not in exc:
            raise
