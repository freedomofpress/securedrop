#!/usr/bin/env python
import os
import shutil
import tempfile
import unittest
import re

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
    gpg = gnupg.GPG(gnupghome=config.GPG_KEY_DIR)

    # Import the journalist key for testing (faster to import a pre-generated
    # key than to gen a new one every time)
    for keyfile in ("test_journalist_key.pub", "test_journalist_key.sec"):
        gpg.import_keys(open(keyfile).read())

def tearDownModule():
    shutil.rmtree(config.TEST_DIR)

class TestSource(unittest.TestCase):

    def _find_codename(self, body):
        # Codenames may contain HTML escape characters, and the wordlist
        # contains various symbols.
        codename_re = r'<p id="code-name" class="code-name">(?P<codename>[a-z0-9 &#;?:=@_.*+()\'"$%!]+)</p>'
        codename_match = re.search(codename_re, body)
        if not codename_match: # debugging
            print body
        self.assertIsNotNone(codename_match)
        return codename_match.group('codename')

    def _navigate_to_create_page(self):
        res = self.app.get('/').click(href='/generate/')
        codename = self._find_codename(res.normal_body)
        res = res.forms['create-form'].submit()
        return res, codename

    def setUp(self):
        middleware = []
        self.app = TestApp(source_app.wsgifunc(*middleware))

    def test_index(self):
        res = self.app.get('/')
        self.assertEqual(res.status, 200)
        self.assertIn("Submit documents for the first time", res.normal_body)
        self.assertIn("Already submitted something?", res.normal_body)

    def test_index_click_submit_documents(self):
        # The "Submit Documents" button is a form submit button
        res = self.app.get('/').click(href='/generate/')
        self.assertEqual(res.status, 200)
        self.assertIn("To protect your identity, we're assigning you a code name.", res.normal_body)
        codename = self._find_codename(res.normal_body)
        self.assertGreater(len(codename), 0)

    def test_generate_click_continue(self):
        res, codename = self._navigate_to_create_page()
        self.assertIn("Upload a file:", res.normal_body)
        self.assertIn("Or just enter a message:", res.normal_body)
        self.assertIn(codename, res.normal_body)

    def test_create_submit_message(self):
        res, codename = self._navigate_to_create_page()
        upload_form = res.forms['upload']
        upload_form.set('msg', 'For your eyes only')
        res = upload_form.submit()
        self.assertEqual(res.status, 200)
        self.assertIn("Thanks! We received your message.", res.normal_body)

    def test_create_submit_file(self):
        # TODO: i don't know if I can mock file uploads with Paste... :(
        pass

    def test_create_submit_both(self):
        pass

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
