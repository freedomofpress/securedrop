#!/usr/bin/env python
import os
import shutil
import tempfile
import unittest
import re
from time import sleep

import gnupg
from paste.fixture import TestApp
from bs4 import BeautifulSoup

# Set the environment variable so config.py uses a test environment
os.environ['DEADDROPENV'] = 'test'
import config, crypto

from source import app as source_app
from journalist import app as journalist_app

def setUpModule():
    pass

def tearDownModule():
    pass

class TestSecureDrop(unittest.TestCase):

    def setUp(self):
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
        self.gpg = gnupg.GPG(gnupghome=config.GPG_KEY_DIR)

        # Import the journalist key for testing (faster to import a pre-generated
        # key than to gen a new one every time)
        for keyfile in ("test_journalist_key.pub", "test_journalist_key.sec"):
            self.gpg.import_keys(open(keyfile).read())

        middleware = []
        self.source_app = TestApp(source_app.wsgifunc(*middleware))
        self.journalist_app = TestApp(journalist_app.wsgifunc(*middleware))

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
        res = self.source_app.get('/').click(href='/generate/')
        codename = self._find_codename(res.normal_body)
        res = res.forms['create-form'].submit()
        return res, codename

    def _do_submission(self, msg=None, doc=None):
        res, codename = self._navigate_to_create_page()
        upload_form = res.forms['upload']
        if msg:
            upload_form.set('msg', msg)
        upload_files = []
        if doc:
            # doc should be a tuple (filename, contents)
            assert isinstance(doc, tuple) and len(doc) == 2
            upload_files = [('fh', doc[0], doc[1])]
        res = self.source_app.post(upload_form.action,
                params=upload_form.submit_fields(),
                upload_files=upload_files)
        return res, codename

    def test_source_index(self):
        res = self.source_app.get('/')
        self.assertEqual(res.status, 200)
        self.assertIn("Submit documents for the first time", res.normal_body)
        self.assertIn("Already submitted something?", res.normal_body)

    def test_journalist_index(self):
        res = self.journalist_app.get('/')
        self.assertEqual(res.status, 200)
        self.assertIn("Latest submissions", res.normal_body)
        self.assertIn("Here are the various collections of documents that have been submitted, with the most recently updated first:", res.normal_body)

    def test_index_click_submit_documents(self):
        # The "Submit Documents" button is a form submit button
        res = self.source_app.get('/').click(href='/generate/')
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
        # Submit the message through the source app
        test_msg = 'This msg is for your eyes only'
        res, codename = self._do_submission(msg=test_msg)
        self.assertEqual(res.status, 200)
        self.assertIn("Thanks! We received your message.", res.normal_body)

        # Check the journalist app for the submitted message
        res = self.journalist_app.get('/')
        soup = BeautifulSoup(res.normal_body)
        self.assertEqual(len(soup.find_all('li')), 1) # we only submitted one message

        # Go to the source submissions page
        source_page_url = '/' + soup.li.a['href']
        res = self.journalist_app.get(source_page_url)
        self.assertIn("Read documents", res.normal_body)

        # Download the submission
        soup = BeautifulSoup(res.normal_body)
        self.assertEqual(len(soup.find_all('li')), 1) # we only submitted one message
        submission_url = source_page_url + soup.li.a['href']
        res = self.journalist_app.get(submission_url)
        decrypted_data = self.gpg.decrypt(res.body)
        self.assertTrue(decrypted_data.ok)
        self.assertEqual(decrypted_data.data, test_msg)

    def test_create_submit_file(self):
        # Submit the file through the source app
        test_filename = 'secrets.txt'
        test_file_contents = 'This file is for your eyes only'
        res, codename = self._do_submission(
                doc=(test_filename, test_file_contents))
        self.assertEqual(res.status, 200)
        self.assertIn("Thanks! We received your document '%s'." % test_filename,
                res.normal_body)

        # Check the journalist app for the submitted file
        res = self.journalist_app.get('/')
        soup = BeautifulSoup(res.normal_body)
        self.assertEqual(len(soup.find_all('li')), 1) # we only submitted one message

        # Go to the source submissions page
        source_page_url = '/' + soup.li.a['href']
        res = self.journalist_app.get(source_page_url)
        self.assertIn("Read documents", res.normal_body)

        # Download the submission
        soup = BeautifulSoup(res.normal_body)
        self.assertEqual(len(soup.find_all('li')), 1) # we only submitted one message
        submission_url = source_page_url + soup.li.a['href']
        res = self.journalist_app.get(submission_url)
        decrypted_data = self.gpg.decrypt(res.body)
        self.assertTrue(decrypted_data.ok)
        self.assertEqual(decrypted_data.data, test_file_contents)
        # TODO: test the filename (encoding with gpg2 --set-filename; unclear
        # if it can be accessed using the gnupg library)

    def test_create_submit_both(self):
        test_msg = 'This msg is for your eyes only'
        test_filename = 'secrets.txt'
        test_file_contents = 'This file is for your eyes only'
        res, codename = self._do_submission(msg=test_msg,
                doc=(test_filename, test_file_contents))
        self.assertEqual(res.status, 200)
        # TODO: should we specifically mention receiving a message when both
        # a message and a document are uploaded simultaneously?
        self.assertIn("Thanks! We received your document '%s'." % test_filename,
                res.normal_body)

        # Check the journalist app for the submitted file
        res = self.journalist_app.get('/')
        soup = BeautifulSoup(res.normal_body)
        self.assertEqual(len(soup.find_all('li')), 1)

        # Go to the source submissions page
        source_page_url = '/' + soup.li.a['href']
        res = self.journalist_app.get(source_page_url)
        self.assertIn("Read documents", res.normal_body)

        # Download the submissions
        soup = BeautifulSoup(res.normal_body)
        submissions = [li.a['href'] for li in soup.find_all('li')]
        self.assertEqual(len(submissions), 2)
        for submission in submissions:
            submission_url = source_page_url + submission
            res = self.journalist_app.get(submission_url)
            decrypted_data = self.gpg.decrypt(res.body)
            self.assertTrue(decrypted_data.ok)
            if '_msg' in submission:
                self.assertEqual(decrypted_data.data, test_msg)
            elif '_doc' in submission:
                self.assertEqual(decrypted_data.data, test_file_contents)

    def test_journalist_reply(self):
        # Submit the message through the source app
        test_msg = 'This msg is for your eyes only'
        res, codename = self._do_submission(msg=test_msg)

        # Wait until the source key has been generated...
        # (the reply form won't be available unless the key exists)
        source_id = crypto.shash(codename)
        while not crypto.getkey(source_id):
            sleep(0.1)

        # Check the journalist app for the submitted message
        res = self.journalist_app.get('/')
        soup = BeautifulSoup(res.normal_body)
        res = res.click(href=soup.li.a['href'])

        # Send a reply to the source
        test_reply = "Thanks for sharing this. We'll follow up soon."
        res.form.set('msg', test_reply)
        res = res.form.submit()
        self.assertIn("Thanks! Your reply has been stored.", res.normal_body)

        # Check the source page for a reply
        res = self.source_app.get('/lookup/')
        res.form.set('id', codename)
        res = res.form.submit()
        self.assertIn("You have received a reply. For your security, please delete all replies when you're done with them.", res.normal_body)
        soup = BeautifulSoup(res.normal_body)
        message = soup.find_all('blockquote', class_='message')[0].text
        self.assertEquals(message, test_reply)

    def tearDown(self):
        shutil.rmtree(config.TEST_DIR)

if __name__ == "__main__":
    unittest.main()
