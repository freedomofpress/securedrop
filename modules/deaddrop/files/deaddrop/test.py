#!/usr/bin/env python
import os
import shutil
import tempfile
import unittest
import re
from cStringIO import StringIO
import zipfile
from time import sleep

import gnupg
from flask import session, g, escape
from flask_testing import TestCase
from flask_wtf import CsrfProtect
from bs4 import BeautifulSoup

# Set environment variable so config.py uses a test environment
os.environ['SECUREDROP_ENV'] = 'test'
import config, crypto_util, store
import source, journalist

def _block_on_reply_keypair_gen(codename):
    sid = crypto_util.shash(codename)
    while not crypto_util.getkey(sid): sleep(0.1)

def _setup_test_docs(sid, files):
    filenames = [ os.path.join(config.STORE_DIR, sid, file) for file in files ]
    for filename in filenames:
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filename, 'w') as fp:
            fp.write('test')
    return filenames

def shared_setup():
    """Set up the file system and GPG"""
    # Create directories for the file store and the GPG keyring
    for d in (config.TEST_DIR, config.STORE_DIR, config.GPG_KEY_DIR, config.TEMP_DIR):
        try:
            os.mkdir(d)
        except OSError:
            # some of these dirs already exist because we import source and
            # journalist, which import crypto_util, which calls gpg.GPG at module
            # level, which auto-generates the GPG homedir if it does not exist
            pass
    # Initialize the GPG keyring
    gpg = gnupg.GPG(gnupghome=config.GPG_KEY_DIR)
    # Import the journalist key for testing (faster to import a pre-generated
    # key than to gen a new one every time)
    for keyfile in ("test_journalist_key.pub", "test_journalist_key.sec"):
        gpg.import_keys(open(keyfile).read())

def shared_teardown():
    shutil.rmtree(config.TEST_DIR)

class TestSource(TestCase):

    @classmethod
    def setUpClass(cls):
        shared_setup()

    @classmethod
    def tearDownClass(cls):
        shared_teardown()

    def create_app(self):
        return source.app

    def test_index(self):
        """Test that the landing page loads and looks how we expect"""
        response = self.client.get('/')
        self.assert200(response)
        self.assertIn("Submit documents for the first time", response.data)
        self.assertIn("Already submitted something?", response.data)

    def _find_codename(self, html):
        """Find a source codename (diceware passphrase) in HTML"""
        # Codenames may contain HTML escape characters, and the wordlist
        # contains various symbols.
        codename_re = r'<p id="code-name" class="code-name">(?P<codename>[a-z0-9 &#;?:=@_.*+()\'"$%!-]+)</p>'
        codename_match = re.search(codename_re, html)
        self.assertIsNotNone(codename_match)
        return codename_match.group('codename')

    def test_generate(self):
        with self.client as c:
            rv = c.get('/generate')
            self.assert200(rv)
            session_codename = session['codename']
        self.assertIn("Submit documents for the first time", rv.data)
        self.assertIn("To protect your identity, we're assigning you a code name.", rv.data)
        codename = self._find_codename(rv.data)
        # default codename length is 8 words
        self.assertEquals(len(codename.split()), 8)
        # codename is also stored in the session - make sure it matches the
        # codename displayed to the source
        self.assertEquals(codename, escape(session_codename))

    def test_regenerate_valid_lengths(self):
        """Make sure we can regenerate all valid length codenames"""
        for codename_len in xrange(4,11):
            response = self.client.post('/generate', data = {
                'number-words': str(codename_len),
            })
            self.assert200(response)
            codename = self._find_codename(response.data)
            self.assertEquals(len(codename.split()), codename_len)

    def test_regenerate_invalid_lengths(self):
        """If the codename length is invalid, it should return 403 Forbidden"""
        for codename_len in (2, 999):
            response = self.client.post('/generate', data = {
                'number-words': str(codename_len),
            })
            self.assert403(response)

    def test_create(self):
        with self.client as c:
            rv = c.get('/generate')
            codename = session['codename']
            rv = c.post('/create', follow_redirects=True)
            self.assertTrue(session['logged_in'])
            # should be redirected to /lookup
            self.assertIn("Upload documents", rv.data)

    def _new_codename(self):
        """Helper function to go through the "generate codename" flow"""
        with self.client as c:
            rv = c.get('/generate')
            codename = session['codename']
            rv = c.post('/create')
        return codename

    def test_login(self):
        rv = self.client.get('/login')
        self.assert200(rv)
        self.assertIn("Already submitted something?", rv.data)

        codename = self._new_codename()
        rv = self.client.post('/login', data=dict(codename=codename),
                follow_redirects=True)
        self.assert200(rv)
        self.assertIn("Upload documents", rv.data)

        rv = self.client.post('/login', data=dict(codename='invalid'),
                follow_redirects=True)
        self.assert200(rv)
        self.assertIn('Sorry, that is not a recognized codename.', rv.data)

    def test_submit_message(self):
        codename = self._new_codename()
        rv = self.client.post('/submit', data=dict(
            msg="This is a test.",
            fh=(StringIO(''), ''),
        ), follow_redirects=True)
        self.assert200(rv)
        self.assertIn("Thanks! We received your message.", rv.data)

    def test_submit_file(self):
        codename = self._new_codename()
        rv = self.client.post('/submit', data=dict(
            msg="",
            fh=(StringIO('This is a test'), 'test.txt'),
        ), follow_redirects=True)
        self.assert200(rv)
        self.assertIn(escape("Thanks! We received your document 'test.txt'."),
                rv.data)

    def test_submit_both(self):
        codename = self._new_codename()
        rv = self.client.post('/submit', data=dict(
            msg="This is a test",
            fh=(StringIO('This is a test'), 'test.txt'),
        ), follow_redirects=True)
        self.assert200(rv)
        self.assertIn("Thanks! We received your message.", rv.data)
        self.assertIn(escape("Thanks! We received your document 'test.txt'."),
                rv.data)

    def test_tor2web_warning(self):
        rv = self.client.get('/', headers=[('X-tor2web', 'encrypted')])
        self.assert200(rv)
        self.assertIn("You appear to be using Tor2Web.", rv.data)

class TestJournalist(TestCase):

    def setUp(self):
        shared_setup()

    def tearDown(self):
        shared_teardown()

    def create_app(self):
        return journalist.app

    def test_index(self):
        rv = self.client.get('/')
        self.assert200(rv)
        self.assertIn("Latest submissions", rv.data)
        self.assertIn("No documents have been submitted!", rv.data)

    def test_bulk_download(self):
        sid = 'EQZGCJBRGISGOTC2NZVWG6LILJBHEV3CINNEWSCLLFTUWZJPKJFECLS2NZ4G4U3QOZCFKTTPNZMVIWDCJBBHMUDBGFHXCQ3R'
        files = ['abc1_msg.gpg', 'abc2_msg.gpg']
        filenames = _setup_test_docs(sid, files)

        rv = self.client.post('/bulk', data=dict(
            action='download',
            sid=sid,
            doc_names_selected=filenames
        ))
        
        self.assertEqual(rv.status_code, 200)

class TestIntegration(unittest.TestCase):

    def setUp(self):
        shared_setup()
        self.source_app = source.app.test_client()
        self.journalist_app = journalist.app.test_client()
        self.gpg = gnupg.GPG(gnupghome=config.GPG_KEY_DIR)

    def tearDown(self):
        shared_teardown()

    def test_submit_message(self):
        """When a source creates an account, test that a new entry appears in the journalist interface"""
        test_msg = "This is a test message."

        with self.source_app as source_app:
            rv = source_app.get('/generate')
            rv = source_app.post('/create', follow_redirects=True)
            codename = session['codename']
            sid = g.sid
        # redirected to submission form
        rv = self.source_app.post('/submit', data=dict(
            msg=test_msg,
            fh=(StringIO(''), ''),
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)

        rv = self.journalist_app.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Latest submissions", rv.data)
        soup = BeautifulSoup(rv.data)
        col_url = soup.select('ul#cols > li a')[0]['href']

        rv = self.journalist_app.get(col_url)
        self.assertEqual(rv.status_code, 200)
        soup = BeautifulSoup(rv.data)
        submission_url = soup.select('ul#submissions li a')[0]['href']
        self.assertIn("_msg", submission_url)
        li = soup.select('ul#submissions li')[0]
        self.assertRegexpMatches(li.contents[-1], "\d+ bytes")

        rv = self.journalist_app.get(submission_url)
        self.assertEqual(rv.status_code, 200)
        decrypted_data = self.gpg.decrypt(rv.data)
        self.assertTrue(decrypted_data.ok)
        self.assertEqual(decrypted_data.data, test_msg)

        # delete submission
        rv = self.journalist_app.get(col_url)
        self.assertEqual(rv.status_code, 200)
        soup = BeautifulSoup(rv.data)
        doc_name = soup.select('ul > li > input[name="doc_names_selected"]')[0]['value']
        rv = self.journalist_app.post('/bulk', data=dict(
            action='delete',
            sid=sid,
            doc_names_selected=doc_name
        ))

        self.assertEqual(rv.status_code, 200)
        soup = BeautifulSoup(rv.data)
        self.assertIn("The following file has been selected for", rv.data)

        # confirm delete submission
        doc_name = soup.select
        doc_name = soup.select('ul > li > input[name="doc_names_selected"]')[0]['value']
        rv = self.journalist_app.post('/bulk', data=dict(
            action='delete',
            sid=sid,
            doc_names_selected=doc_name,
            confirm_delete="1"
        ))
        self.assertEqual(rv.status_code, 200)
        soup = BeautifulSoup(rv.data)
        self.assertIn("File permanently deleted.", rv.data)

        # confirm that submission deleted and absent in list of submissions
        rv = self.journalist_app.get(col_url)
        self.assertEqual(rv.status_code, 200)
        self.assertIn("No documents to display.", rv.data)

    def test_submit_file(self):
        """When a source creates an account, test that a new entry appears in the journalist interface"""
        test_file_contents = "This is a test file."
        test_filename = "test.txt"

        with self.source_app as source_app:
            rv = source_app.get('/generate')
            rv = source_app.post('/create', follow_redirects=True)
            codename = session['codename']
            sid = g.sid
        # redirected to submission form
        rv = self.source_app.post('/submit', data=dict(
            msg="",
            fh=(StringIO(test_file_contents), test_filename),
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)

        rv = self.journalist_app.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Latest submissions", rv.data)
        soup = BeautifulSoup(rv.data)
        col_url = soup.select('ul#cols > li a')[0]['href']

        rv = self.journalist_app.get(col_url)
        self.assertEqual(rv.status_code, 200)
        soup = BeautifulSoup(rv.data)
        submission_url = soup.select('ul#submissions li a')[0]['href']
        self.assertIn("_doc", submission_url)
        li = soup.select('ul#submissions li')[0]
        self.assertRegexpMatches(li.contents[-1], "\d+ bytes")

        rv = self.journalist_app.get(submission_url)
        self.assertEqual(rv.status_code, 200)
        decrypted_data = self.gpg.decrypt(rv.data)
        self.assertTrue(decrypted_data.ok)

        s = StringIO(decrypted_data.data)
        zip_file = zipfile.ZipFile(s, 'r')
        unzipped_decrypted_data = zip_file.read('test.txt')
        zip_file.close()

        self.assertEqual(unzipped_decrypted_data, test_file_contents)

        # delete submission
        rv = self.journalist_app.get(col_url)
        self.assertEqual(rv.status_code, 200)
        soup = BeautifulSoup(rv.data)
        doc_name = soup.select('ul > li > input[name="doc_names_selected"]')[0]['value']
        rv = self.journalist_app.post('/bulk', data=dict(
            action='delete',
            sid=sid,
            doc_names_selected=doc_name
        ))

        self.assertEqual(rv.status_code, 200)
        soup = BeautifulSoup(rv.data)
        self.assertIn("The following file has been selected for", rv.data)

        # confirm delete submission
        doc_name = soup.select
        doc_name = soup.select('ul > li > input[name="doc_names_selected"]')[0]['value']
        rv = self.journalist_app.post('/bulk', data=dict(
            action='delete',
            sid=sid,
            doc_names_selected=doc_name,
            confirm_delete="1"
        ))
        self.assertEqual(rv.status_code, 200)
        soup = BeautifulSoup(rv.data)
        self.assertIn("File permanently deleted.", rv.data)

        # confirm that submission deleted and absent in list of submissions
        rv = self.journalist_app.get(col_url)
        self.assertEqual(rv.status_code, 200)
        self.assertIn("No documents to display.", rv.data)

    def test_reply(self):
        test_msg = "This is a test message."
        test_reply = "This is a test reply."

        with self.source_app as source_app:
            rv = source_app.get('/generate')
            rv = source_app.post('/create', follow_redirects=True)
            codename = session['codename']
            flagged = session['flagged']
            sid = g.sid
        # redirected to submission form
        rv = self.source_app.post('/submit', data=dict(
            msg=test_msg,
            fh=(StringIO(''), ''),
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertFalse(flagged)

        rv = self.journalist_app.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Latest submissions", rv.data)
        soup = BeautifulSoup(rv.data)
        col_url = soup.select('ul#cols > li a')[0]['href']

        rv = self.journalist_app.get(col_url)
        self.assertEqual(rv.status_code, 200)

        with self.source_app as source_app:
            rv = source_app.post('/login', data=dict(
                codename=codename), follow_redirects=True)
            self.assertEqual(rv.status_code, 200)
            self.assertFalse(session['flagged'])

        rv = self.journalist_app.post('/flag', data=dict(
            sid=sid))
        self.assertEqual(rv.status_code, 200)

        with self.source_app as source_app:
            rv = source_app.post('/login', data=dict(
                codename=codename), follow_redirects=True)
            self.assertEqual(rv.status_code, 200)
            self.assertTrue(session['flagged'])
            source_app.get('/lookup')
            self.assertTrue(g.flagged)

        # Block until the reply keypair has been generated, so we can test
        # sending a reply
        _block_on_reply_keypair_gen(codename)

        rv = self.journalist_app.post('/reply', data=dict(
            sid=sid,
            msg=test_reply
        ))
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Thanks! Your reply has been stored.", rv.data)

        rv = self.journalist_app.get(col_url)
        self.assertIn("reply-", rv.data)

        _block_on_reply_keypair_gen(codename)
        rv = self.source_app.get('/lookup')
        self.assertEqual(rv.status_code, 200)
        self.assertIn("You have received a reply. For your security, please delete all replies when you're done with them.", rv.data)
        self.assertIn(test_reply, rv.data)

        soup = BeautifulSoup(rv.data)
        msgid = soup.select('form.message > input[name="msgid"]')[0]['value']
        rv = self.source_app.post('/delete', data=dict(
            sid=sid,
            msgid=msgid,
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Reply deleted", rv.data)

class TestStore(unittest.TestCase):
    '''The set of tests for store.py.'''
    @classmethod
    def setUp(self):
        shared_setup()

    @classmethod
    def tearDown(self):
        shared_teardown()

    def test_verify(self):
        with self.assertRaises(store.PathException):
            store.verify(os.path.join(config.STORE_DIR, '..', 'etc', 'passwd'))

    def test_get_zip(self):
        sid = 'EQZGCJBRGISGOTC2NZVWG6LILJBHEV3CINNEWSCLLFTUWZJPKJFECLS2NZ4G4U3QOZCFKTTPNZMVIWDCJBBHMUDBGFHXCQ3R'
        files = ['abc1_msg.gpg', 'abc2_msg.gpg']
        filenames = _setup_test_docs(sid, files)

        zip = store.get_bulk_archive(filenames)

        zipfile_contents = zipfile.ZipFile(zip).namelist()
        for file in files:
            self.assertIn(file, zipfile_contents)

if __name__ == "__main__":
    unittest.main(verbosity=2)
