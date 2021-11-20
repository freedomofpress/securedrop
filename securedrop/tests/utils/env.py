# -*- coding: utf-8 -*-
"""Testing utilities related to setup and teardown of test environment.
"""
import os
import shutil
import threading
from os.path import abspath
from os.path import dirname
from os.path import isdir
from os.path import join
from os.path import realpath

from db import db

os.environ['SECUREDROP_ENV'] = 'test'  # noqa


TESTS_DIR = abspath(join(dirname(realpath(__file__)), '..'))


def create_directories(config):
    """Create directories for the file store and the GPG keyring.
    """
    for d in (config.SECUREDROP_DATA_ROOT, config.STORE_DIR,
              config.GPG_KEY_DIR, config.TEMP_DIR):
        if not isdir(d):
            os.mkdir(d)


def teardown(config):
    # make sure threads launched by tests complete before
    # teardown, otherwise they may fail because resources
    # they need disappear
    for t in threading.enumerate():
        if t.is_alive() and not isinstance(t, threading._MainThread):
            t.join()
    db.session.remove()
    try:
        shutil.rmtree(config.TEMP_DIR)
    except OSError:
        # Then check the directory was already deleted
        assert not os.path.exists(config.TEMP_DIR)
    try:
        shutil.rmtree(config.SECUREDROP_DATA_ROOT)
        # safeguard for #844
        assert not os.path.exists(config.SECUREDROP_DATA_ROOT)
    except OSError as exc:
        if 'No such file or directory' != exc.strerror:
            raise
