# -*- coding: utf-8 -*-
"""Testing utilities related to setup and teardown of test environment.
"""
import os
import shutil
import threading
from pathlib import Path
from os.path import abspath
from os.path import dirname
from os.path import isdir
from os.path import join
from os.path import realpath

from db import db


TESTS_DIR = abspath(join(dirname(realpath(__file__)), '..'))


def create_directories(config):
    """Create directories for the file store.
    """
    # config.SECUREDROP_DATA_ROOT and config.GPG_KEY_DIR already get created by the
    # setup_journalist_key_and_gpg_folder fixture
    for d in [config.STORE_DIR, config.TEMP_DIR]:
        if not isdir(d):
            os.mkdir(d)


def teardown(config):
    # make sure threads launched by tests complete before
    # teardown, otherwise they may fail because resources
    # they need disappear
    for t in threading.enumerate():
        if t.is_alive() and not isinstance(t, threading._MainThread):
            t.join()

    # Delete the DB file
    db.session.remove()
    Path(config.DATABASE_FILE).unlink()

    # Delete other directories
    for config_dir in [config.TEMP_DIR, config.STORE_DIR]:
        try:
            shutil.rmtree(config_dir)
        except OSError:
            # Then check the directory was already deleted
            assert not os.path.exists(config_dir)
