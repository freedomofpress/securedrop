#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import shutil
import tempfile
import unittest
import re
from cStringIO import StringIO
import zipfile
from time import sleep
import uuid
from mock import patch, ANY

import gnupg
from flask import session, g, escape
from flask_wtf import CsrfProtect
from bs4 import BeautifulSoup

# Set environment variable so config.py uses a test environment
os.environ['SECUREDROP_ENV'] = 'test'
import config
import crypto_util
import store
import source
import journalist
import test_setup
from db import db_session, Source

def _block_on_reply_keypair_gen(codename):
    sid = crypto_util.hash_codename(codename)
    while not crypto_util.getkey(sid):
        sleep(0.1)

def _logout(test_client):
    # See http://flask.pocoo.org/docs/testing/#accessing-and-modifying-sessions
    # This is necessary because SecureDrop doesn't have a logout button, so a
    # user is logged in until they close the browser, which clears the session.
    # For testing, this function simulates closing the browser at places
    # where a source is likely to do so (for instance, between submitting a
    # document and checking for a journalist reply).
    with test_client.session_transaction() as sess:
        sess.clear()

def shared_setup():
    """Set up the file system, GPG, and database"""
    test_setup.create_directories()
    test_setup.init_gpg()
    test_setup.init_db()

    # Do tests that should always run on app startup
    crypto_util.do_runtime_tests()

def shared_teardown():
    test_setup.clean_root()


class TestSource(unittest.TestCase):

    def setUp(self):
        shared_setup()
        self.app = source.app
        self.client = self.app.test_client()

    def tearDown(self):
        shared_teardown()

    def test_index(self):
        """Test that the landing page loads and looks how we expect"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Submit documents for the first time", response.data)
        self.assertIn("Already submitted something?", response.data)

    def _find_codename(self, html):
        """Find a source codename (diceware passphrase) in HTML"""
        # Codenames may contain HTML escape characters, and the wordlist
        # contains various symbols.
        codename_re = r'<strong id="codename">(?P<codename>[a-z0-9 &#;?:=@_.*+()\'"$%!-]+)</strong>'
        codename_match = re.search(codename_re, html)
        self.assertIsNotNone(codename_match)
        return codename_match.group('codename')

    def test_generate(self):
        with self.client as c:
            rv = c.get('/generate')
            self.assertEqual(rv.status_code, 200)
            session_codename = session['codename']
        self.assertIn("Remember this code and keep it secret", rv.data)
        self.assertIn(
            "To protect your identity, we're assigning you a unique code name.", rv.data)
        codename = self._find_codename(rv.data)
        # default codename length is 8 words
        self.assertEqual(len(codename.split()), 8)
        # codename is also stored in the session - make sure it matches the
        # codename displayed to the source
        self.assertEqual(codename, escape(session_codename))

    def test_regenerate_valid_lengths(self):
        """Make sure we can regenerate all valid length codenames"""
        for codename_len in xrange(7, 11):
            response = self.client.post('/generate', data={
                'number-words': str(codename_len),
            })
            self.assertEqual(response.status_code, 200)
            codename = self._find_codename(response.data)
            self.assertEquals(len(codename.split()), codename_len)

    def test_regenerate_invalid_lengths(self):
        """If the codename length is invalid, it should return 403 Forbidden"""
        for codename_len in (2, 999):
            response = self.client.post('/generate', data={
                'number-words': str(codename_len),
            })
            self.assertEqual(response.status_code, 403)

    def test_generate_has_login_link(self):
        """The generate page should have a link to remind people to login if they already have a codename, rather than create a new one."""
        rv = self.client.get('/generate')
        self.assertIn("Already have a codename?", rv.data)
        soup = BeautifulSoup(rv.data)
        already_have_codename_link = soup.select('a#already-have-codename')[0]
        self.assertEqual(already_have_codename_link['href'], '/login')

    def test_create(self):
        with self.client as c:
            rv = c.get('/generate')
            codename = session['codename']
            rv = c.post('/create', follow_redirects=True)
            self.assertTrue(session['logged_in'])
            # should be redirected to /lookup
            self.assertIn("You have three options to send data", rv.data)

    def _new_codename(self):
        """Helper function to go through the "generate codename" flow"""
        with self.client as c:
            rv = c.get('/generate')
            codename = session['codename']
            rv = c.post('/create')
        return codename

    def test_lookup(self):
        """Test various elements on the /lookup page"""
        codename = self._new_codename()
        rv = self.client.post('login', data=dict(codename=codename),
                              follow_redirects=True)
        # redirects to /lookup
        self.assertIn("journalist's public key", rv.data)
        # download the public key
        rv = self.client.get('journalist-key')
        self.assertIn("BEGIN PGP PUBLIC KEY BLOCK", rv.data)

    def test_login_and_logout(self):
        rv = self.client.get('/login')
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Login to check for responses", rv.data)

        codename = self._new_codename()
        with self.client as c:
            rv = c.post('/login', data=dict(codename=codename),
                                  follow_redirects=True)
            self.assertEqual(rv.status_code, 200)
            self.assertIn("You have three options to send data", rv.data)
            self.assertTrue(session['logged_in'])
            _logout(c)

        with self.client as c:
            rv = self.client.post('/login', data=dict(codename='invalid'),
                                  follow_redirects=True)
            self.assertEqual(rv.status_code, 200)
            self.assertIn('Sorry, that is not a recognized codename.', rv.data)
            self.assertNotIn('logged_in', session)

    def test_submit_message(self):
        self._new_codename()
        rv = self.client.post('/submit', data=dict(
            msg="This is a test.",
            fh=(StringIO(''), ''),
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Thanks! We received your message.", rv.data)

    def test_submit_file(self):
        self._new_codename()
        rv = self.client.post('/submit', data=dict(
            msg="",
            fh=(StringIO('This is a test'), 'test.txt'),
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn(escape("Thanks! We received your document 'test.txt'."),
                      rv.data)

    def test_submit_both(self):
        self._new_codename()
        rv = self.client.post('/submit', data=dict(
            msg="This is a test",
            fh=(StringIO('This is a test'), 'test.txt'),
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Thanks! We received your message.", rv.data)
        self.assertIn(escape("Thanks! We received your document 'test.txt'."),
                      rv.data)

    def test_submit_dirty_file_to_be_cleaned(self):
        self.gpg = gnupg.GPG(homedir=config.GPG_KEY_DIR)
        img = open(os.getcwd()+'/tests/test_images/dirty.jpg')
        img_metadata = store.metadata_handler(img.name)
        self.assertFalse(img_metadata.is_clean(), "The file is dirty.")
        codename = self._new_codename()
        rv = self.client.post('/submit', data=dict(
            msg="",
            fh=(img, 'dirty.jpg'),
            notclean='True',
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn(escape("Thanks! We received your document 'dirty.jpg'."),
                      rv.data)

        store_dirs = [os.path.join(config.STORE_DIR,d) for d in os.listdir(config.STORE_DIR) if os.path.isdir(os.path.join(config.STORE_DIR,d))]
        latest_subdir = max(store_dirs, key=os.path.getmtime)
        zip_gpg_files = [os.path.join(latest_subdir,f) for f in os.listdir(latest_subdir) if os.path.isfile(os.path.join(latest_subdir,f))]
        self.assertEqual(len(zip_gpg_files), 1)
        zip_gpg = zip_gpg_files[0]

        zip_gpg_file = open(zip_gpg)
        decrypted_data = self.gpg.decrypt_file(zip_gpg_file)
        self.assertTrue(decrypted_data.ok, 'Checking the integrity of the data after decryption.')

        s = StringIO(decrypted_data.data)
        zip_file = zipfile.ZipFile(s, 'r')
        clean_file = open(os.path.join(latest_subdir,'dirty.jpg'), 'w+b')
        clean_file.write(zip_file.read('dirty.jpg'))
        clean_file.seek(0)
        zip_file.close()

        # check for the actual file been clean
        clean_file_metadata = store.metadata_handler(clean_file.name)
        self.assertTrue(clean_file_metadata.is_clean(), "the file is now clean.")
        zip_gpg_file.close()
        clean_file.close()
        img.close()

    def test_submit_dirty_file_to_not_clean(self):
        self.gpg = gnupg.GPG(homedir=config.GPG_KEY_DIR)
        img = open(os.getcwd()+'/tests/test_images/dirty.jpg')
        img_metadata = store.metadata_handler(img.name)
        self.assertFalse(img_metadata.is_clean(), "The file is dirty.")
        codename = self._new_codename()
        rv = self.client.post('/submit', data=dict(
            msg="",
            fh=(img, 'dirty.jpg'),
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn(escape("Thanks! We received your document 'dirty.jpg'."),
                      rv.data)

        store_dirs = [os.path.join(config.STORE_DIR,d) for d in os.listdir(config.STORE_DIR) if os.path.isdir(os.path.join(config.STORE_DIR,d))]
        latest_subdir = max(store_dirs, key=os.path.getmtime)
        zip_gpg_files = [os.path.join(latest_subdir,f) for f in os.listdir(latest_subdir) if os.path.isfile(os.path.join(latest_subdir,f))]
        self.assertEqual(len(zip_gpg_files), 1)
        zip_gpg = zip_gpg_files[0]

        zip_gpg_file = open(zip_gpg)
        decrypted_data = self.gpg.decrypt_file(zip_gpg_file)
        self.assertTrue(decrypted_data.ok, 'Checking the integrity of the data after decryption.')

        s = StringIO(decrypted_data.data)
        zip_file = zipfile.ZipFile(s, 'r')
        clean_file = open(os.path.join(latest_subdir,'dirty.jpg'), 'w+b')
        clean_file.write(zip_file.read('dirty.jpg'))
        clean_file.seek(0)
        zip_file.close()

        # check for the actual file been clean
        clean_file_metadata = store.metadata_handler(clean_file.name)
        self.assertFalse(clean_file_metadata.is_clean(), "the file is was not cleaned.")
        zip_gpg_file.close()
        clean_file.close()
        img.close()

    def test_submit_clean_file(self):
        img = open(os.getcwd()+'/tests/test_images/clean.jpg')
        codename = self._new_codename()
        rv = self.client.post('/submit', data=dict(
            msg="This is a test",
            fh=(img, 'clean.jpg'),
            notclean='True',
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Thanks! We received your message.", rv.data)
        self.assertIn(escape("Thanks! We received your document 'clean.jpg'."),
                      rv.data)
        img.close()

    @patch('zipfile.ZipFile.writestr')
    def test_submit_sanitizes_filename(self, zipfile_write):
        """Test that upload file name is sanitized"""
        insecure_filename = '../../bin/gpg'
        sanitized_filename = 'bin_gpg'

        self._new_codename()
        self.client.post('/submit', data=dict(
            msg="",
            fh=(StringIO('This is a test'), insecure_filename),
        ), follow_redirects=True)
        zipfile_write.assert_called_with(sanitized_filename, ANY)

    def test_tor2web_warning(self):
        rv = self.client.get('/', headers=[('X-tor2web', 'encrypted')])
        self.assertEqual(rv.status_code, 200)
        self.assertIn("You appear to be using Tor2Web.", rv.data)


class TestJournalist(unittest.TestCase):

    def setUp(self):
        shared_setup()
        self.app = journalist.app
        self.client = self.app.test_client()

    def tearDown(self):
        shared_teardown()

    def test_index(self):
        rv = self.client.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Sources", rv.data)
        self.assertIn("No documents have been submitted!", rv.data)

    def test_bulk_download(self):
        sid = 'EQZGCJBRGISGOTC2NZVWG6LILJBHEV3CINNEWSCLLFTUWZJPKJFECLS2NZ4G4U3QOZCFKTTPNZMVIWDCJBBHMUDBGFHXCQ3R'
        source = Source(sid, crypto_util.display_id())
        db_session.add(source)
        db_session.commit()
        files = ['1-abc1-msg.gpg', '2-abc2-msg.gpg']
        filenames = test_setup.setup_test_docs(sid, files)

        rv = self.client.post('/bulk', data=dict(
            action='download',
            sid=sid,
            doc_names_selected=files
        ))

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.content_type, 'application/zip')
        self.assertTrue(zipfile.is_zipfile(StringIO(rv.data)))


class TestIntegration(unittest.TestCase):

    def setUp(self):
        shared_setup()
        self.source_app = source.app.test_client()
        self.journalist_app = journalist.app.test_client()
        self.gpg = gnupg.GPG(homedir=config.GPG_KEY_DIR)

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
            _logout(source_app)

        rv = self.journalist_app.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Sources", rv.data)
        soup = BeautifulSoup(rv.data)
        col_url = soup.select('ul#cols > li a')[0]['href']

        rv = self.journalist_app.get(col_url)
        self.assertEqual(rv.status_code, 200)
        soup = BeautifulSoup(rv.data)
        submission_url = soup.select('ul#submissions li a')[0]['href']
        self.assertIn("-msg", submission_url)
        li = soup.select('ul#submissions li .doc-info')[0]
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
        doc_name = soup.select(
            'ul > li > input[name="doc_names_selected"]')[0]['value']
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
        doc_name = soup.select(
            'ul > li > input[name="doc_names_selected"]')[0]['value']
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
            _logout(source_app)

        rv = self.journalist_app.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Sources", rv.data)
        soup = BeautifulSoup(rv.data)
        col_url = soup.select('ul#cols > li a')[0]['href']

        rv = self.journalist_app.get(col_url)
        self.assertEqual(rv.status_code, 200)
        soup = BeautifulSoup(rv.data)
        submission_url = soup.select('ul#submissions li a')[0]['href']
        self.assertIn("-doc", submission_url)
        li = soup.select('ul#submissions li .doc-info')[0]
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
        doc_name = soup.select(
            'ul > li > input[name="doc_names_selected"]')[0]['value']
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
        doc_name = soup.select(
            'ul > li > input[name="doc_names_selected"]')[0]['value']
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

    def test_reply_normal(self):
        self.helper_test_reply("This is a test reply.", True)

    def test_reply_unicode(self):
        self.helper_test_reply("Teşekkürler", True)

    def helper_test_reply(self, test_reply, expected_success=True):
        test_msg = "This is a test message."

        with self.source_app as source_app:
            rv = source_app.get('/generate')
            rv = source_app.post('/create', follow_redirects=True)
            codename = session['codename']
            sid = g.sid
            # redirected to submission form
            rv = source_app.post('/submit', data=dict(
                msg=test_msg,
                fh=(StringIO(''), ''),
            ), follow_redirects=True)
            self.assertEqual(rv.status_code, 200)
            self.assertFalse(g.source.flagged)
            _logout(source_app)

        rv = self.journalist_app.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Sources", rv.data)
        soup = BeautifulSoup(rv.data)
        col_url = soup.select('ul#cols > li a')[0]['href']

        rv = self.journalist_app.get(col_url)
        self.assertEqual(rv.status_code, 200)

        with self.source_app as source_app:
            rv = source_app.post('/login', data=dict(
                codename=codename), follow_redirects=True)
            self.assertEqual(rv.status_code, 200)
            self.assertFalse(g.source.flagged)
            _logout(source_app)

        with self.journalist_app as journalist_app:
            rv = journalist_app.post('/flag', data=dict(
                sid=sid))
            self.assertEqual(rv.status_code, 200)
            _logout(journalist_app)

        with self.source_app as source_app:
            rv = source_app.post('/login', data=dict(
                codename=codename), follow_redirects=True)
            self.assertEqual(rv.status_code, 200)
            self.assertTrue(g.source.flagged)
            source_app.get('/lookup')
            self.assertTrue(g.source.flagged)
            _logout(source_app)

        # Block until the reply keypair has been generated, so we can test
        # sending a reply
        _block_on_reply_keypair_gen(codename)

        rv = self.journalist_app.post('/reply', data=dict(
            sid=sid,
            msg=test_reply
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)

        if not expected_success:
            pass
        else:
            self.assertIn("Thanks! Your reply has been stored.", rv.data)

        with self.journalist_app as journalist_app:
            rv = journalist_app.get(col_url)
            self.assertIn("reply-", rv.data)
            _logout(journalist_app)

        _block_on_reply_keypair_gen(codename)

        with self.source_app as source_app:
            rv = source_app.post('/login', data=dict(codename=codename), follow_redirects=True)
            self.assertEqual(rv.status_code, 200)
            rv = source_app.get('/lookup')
            self.assertEqual(rv.status_code, 200)

            if not expected_success:
                # there should be no reply
                self.assertTrue("You have received a reply." not in rv.data)
            else:
                self.assertIn(
                    "You have received a reply. For your security, please delete all replies when you're done with them.", rv.data)
                self.assertIn(test_reply, rv.data)
                soup = BeautifulSoup(rv.data)
                msgid = soup.select('form.message > input[name="msgid"]')[0]['value']
                rv = source_app.post('/delete', data=dict(
                        sid=sid,
                        msgid=msgid,
                        ), follow_redirects=True)
                self.assertEqual(rv.status_code, 200)
                self.assertIn("Reply deleted", rv.data)
                _logout(source_app)


    def test_delete_collection(self):
        """Test the "delete collection" button on each collection page"""
        # first, add a source
        self.source_app.get('/generate')
        self.source_app.post('/create')
        self.source_app.post('/submit', data=dict(
            msg="This is a test.",
            fh=(StringIO(''), ''),
        ), follow_redirects=True)

        rv = self.journalist_app.get('/')
        # navigate to the collection page
        soup = BeautifulSoup(rv.data)
        first_col_url = soup.select('ul#cols > li a')[0]['href']
        rv = self.journalist_app.get(first_col_url)
        self.assertEqual(rv.status_code, 200)

        # find the delete form and extract the post parameters
        soup = BeautifulSoup(rv.data)
        delete_form_inputs = soup.select('form#delete_collection')[0]('input')
        sid = delete_form_inputs[1]['value']
        col_name = delete_form_inputs[2]['value']
        rv = self.journalist_app.post('/col/process', data=dict(
            action='delete',
            sid=sid,
            col_name=col_name,
        ), follow_redirects=True)
        self.assertEquals(rv.status_code, 200)

        self.assertIn(escape("%s's collection deleted" % (col_name,)), rv.data)
        self.assertIn("No documents have been submitted!", rv.data)


    def test_delete_collections(self):
        """Test the "delete selected" checkboxes on the index page that can be
        used to delete multiple collections"""
        # first, add some sources
        num_sources = 2
        for i in range(num_sources):
            self.source_app.get('/generate')
            self.source_app.post('/create')
            self.source_app.post('/submit', data=dict(
                msg="This is a test "+str(i)+".",
                fh=(StringIO(''), ''),
            ), follow_redirects=True)
            _logout(self.source_app)

        rv = self.journalist_app.get('/')
        # get all the checkbox values
        soup = BeautifulSoup(rv.data)
        checkbox_values = [ checkbox['value'] for checkbox in
                            soup.select('input[name="cols_selected"]') ]
        rv = self.journalist_app.post('/col/process', data=dict(
            action='delete',
            cols_selected=checkbox_values
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn("%s collections deleted" % (num_sources,), rv.data)

        # TODO: functional tests (selenium)
        # This code just tests the underlying API and *does not* test the
        # interactions due to the Javascript in journalist.js. Once we have
        # functional tests, we should add tests for:
        # 1. Warning dialog appearance
        # 2. "Don't show again" checkbox behavior
        # 2. Correct behavior on "yes" and "no" buttons

    def test_filenames(self):
        """Test pretty, sequential filenames when source uploads messages and files"""
        # add a source and submit stuff
        self.source_app.get('/generate')
        self.source_app.post('/create')
        self.helper_filenames_submit()

        # navigate to the collection page
        rv = self.journalist_app.get('/')
        soup = BeautifulSoup(rv.data)
        first_col_url = soup.select('ul#cols > li a')[0]['href']
        rv = self.journalist_app.get(first_col_url)
        self.assertEqual(rv.status_code, 200)

        # test filenames and sort order
        soup = BeautifulSoup(rv.data)
        submission_filename_re = r'^{0}-[a-z0-9-_]+(-msg|-doc\.zip)\.gpg$'
        for i, submission_link in enumerate(soup.select('ul#submissions li a')):
            filename = str(submission_link.contents[0])
            self.assertTrue(re.match(submission_filename_re.format(i+1), filename))


    def test_filenames_delete(self):
        """Test pretty, sequential filenames when journalist deletes files"""
        # add a source and submit stuff
        self.source_app.get('/generate')
        self.source_app.post('/create')
        self.helper_filenames_submit()

        # navigate to the collection page
        rv = self.journalist_app.get('/')
        soup = BeautifulSoup(rv.data)
        first_col_url = soup.select('ul#cols > li a')[0]['href']
        rv = self.journalist_app.get(first_col_url)
        self.assertEqual(rv.status_code, 200)
        soup = BeautifulSoup(rv.data)

        # delete file #2
        self.helper_filenames_delete(soup, 1)
        rv = self.journalist_app.get(first_col_url)
        soup = BeautifulSoup(rv.data)

        # test filenames and sort order
        submission_filename_re = r'^{0}-[a-z0-9-_]+(-msg|-doc\.zip)\.gpg$'
        filename = str(soup.select('ul#submissions li a')[0].contents[0])
        self.assertTrue( re.match(submission_filename_re.format(1), filename) )
        filename = str(soup.select('ul#submissions li a')[1].contents[0])
        self.assertTrue( re.match(submission_filename_re.format(3), filename) )
        filename = str(soup.select('ul#submissions li a')[2].contents[0])
        self.assertTrue( re.match(submission_filename_re.format(4), filename) )


    def helper_filenames_submit(self):
        self.source_app.post('/submit', data=dict(
            msg="This is a test.",
            fh=(StringIO(''), ''),
        ), follow_redirects=True)
        self.source_app.post('/submit', data=dict(
            msg="This is a test.",
            fh=(StringIO('This is a test'), 'test.txt'),
        ), follow_redirects=True)
        self.source_app.post('/submit', data=dict(
            msg="",
            fh=(StringIO('This is a test'), 'test.txt'),
        ), follow_redirects=True)

    def helper_filenames_delete(self, soup, i):
        sid = soup.select('input[name="sid"]')[0]['value']
        checkbox_values = [soup.select('input[name="doc_names_selected"]')[i]['value']]

        # delete
        rv = self.journalist_app.post('/bulk', data=dict(
            sid=sid,
            action='delete',
            doc_names_selected=checkbox_values
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn("The following file has been selected for <strong>permanent deletion</strong>", rv.data)

        # confirm delete
        rv = self.journalist_app.post('/bulk', data=dict(
            sid=sid,
            action='delete',
            confirm_delete=1,
            doc_names_selected=checkbox_values
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn("File permanently deleted.", rv.data)


class TestStore(unittest.TestCase):

    '''The set of tests for store.py.'''
    def setUp(self):
        shared_setup()

    def tearDown(self):
        shared_teardown()

    def test_verify(self):
        with self.assertRaises(store.PathException):
            store.verify(os.path.join(config.STORE_DIR, '..', 'etc', 'passwd'))
        with self.assertRaises(store.PathException):
            store.verify(config.STORE_DIR + "_backup")

    def test_get_zip(self):
        sid = 'EQZGCJBRGISGOTC2NZVWG6LILJBHEV3CINNEWSCLLFTUWZJPKJFECLS2NZ4G4U3QOZCFKTTPNZMVIWDCJBBHMUDBGFHXCQ3R'
        files = ['1-abc1-msg.gpg', '2-abc2-msg.gpg']
        filenames = test_setup.setup_test_docs(sid, files)

        archive = zipfile.ZipFile(store.get_bulk_archive(filenames))

        archivefile_contents = archive.namelist()

        for archived_file, actual_file in zip(archivefile_contents, filenames):
            actual_file_content = open(actual_file).read()
            zipped_file_content = archive.read(archived_file)
            self.assertEquals(zipped_file_content, actual_file_content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
