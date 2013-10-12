#!/usr/bin/env python
import os
import shutil
import tempfile
import unittest

import gnupg
from paste.fixture import TestApp

# Set the environment variable so config.py uses a test environment
os.environ['DEADDROPENV'] = 'test'
import config
from source import app as source_app
from journalist import app as journalist_app

def setUpModule():
    """Set up the file system and GPG"""
    # Create directories for the file store and the GPG keyring
    for d in (config.TEST_DIR, config.STORE_DIR, config.GPG_KEY_DIR):
        try:
            # some of these dirs already exist because we import source and
            # journalist, which import crypto, which calls gpg.GPG at module
            # level, which auto-generates the GPG homedir if it does not exist
            os.mkdir(d)
        except OSError:
            pass

    # Initialize the GPG keyring
    gpg = gnupg.GPG(homedir=config.GPG_KEY_DIR)

    # Import the journalist key for testing (faster to import a pre-generated
    # key than to gen a new one every time)
    for keyfile in ("test_journalist_key.pub", "test_journalist_key.sec"):
        gpg.import_keys(open(keyfile).read())

def tearDownModule():
    shutil.rmtree(config.TEST_DIR)

class TestSource(unittest.TestCase):
    def setUp(self):
        middleware = []
        self.app = TestApp(source_app.wsgifunc(*middleware))

    def tearDown(self):
        pass

class TestJournalist(unittest.TestCase):
    def setUp(self):
        middleware = []
        self.app = TestApp(journalist_app.wsgifunc(*middleware))

    def tearDown(self):
        pass

if __name__ == "__main__":
    unittest.main()
