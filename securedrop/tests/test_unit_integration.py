#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import unittest
import re
from cStringIO import StringIO
import zipfile
from time import sleep

import gnupg
from flask import session, g, escape
from bs4 import BeautifulSoup

# Set environment variable so config.py uses a test environment
os.environ['SECUREDROP_ENV'] = 'test'
import config
import crypto_util
import source
import journalist
import common
from db import db_session, Journalist


def _block_on_reply_keypair_gen(codename):
    sid = crypto_util.hash_codename(codename)
    while not crypto_util.getkey(sid):
        sleep(0.1)


class TestIntegration(unittest.TestCase):

    def setUp(self):
        common.shared_setup()

        self.source_app = source.app.test_client()
        self.journalist_app = journalist.app.test_client()

        self.gpg = gnupg.GPG(homedir=config.GPG_KEY_DIR)

        # Add a test user to the journalist interface and log them in
        #print Journalist.query.all()
        self.user_pw = "bar"
        self.user = Journalist(username="foo",
                               password=self.user_pw)
        db_session.add(self.user)
        db_session.commit()
        self._login_user()

    def _login_user(self):
        self.journalist_app.post('/login', data=dict(
            username=self.user.username,
            password=self.user_pw,
            token=self.user.totp.now()),
            follow_redirects=True)

    def tearDown(self):
        common.shared_teardown()

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
            common.logout(source_app)

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
        span = soup.select('ul#submissions li span.info span')[0]
        self.assertRegexpMatches(span['title'], "\d+ bytes")

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
            common.logout(source_app)

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
        span = soup.select('ul#submissions li span.info span')[0]
        self.assertRegexpMatches(span['title'], "\d+ bytes")

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
            common.logout(source_app)

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
            common.logout(source_app)

        with self.journalist_app as journalist_app:
            rv = journalist_app.post('/flag', data=dict(
                sid=sid))
            self.assertEqual(rv.status_code, 200)

        with self.source_app as source_app:
            rv = source_app.post('/login', data=dict(
                codename=codename), follow_redirects=True)
            self.assertEqual(rv.status_code, 200)
            self.assertTrue(g.source.flagged)
            source_app.get('/lookup')
            self.assertTrue(g.source.flagged)
            common.logout(source_app)

        # Block until the reply keypair has been generated, so we can test
        # sending a reply
        _block_on_reply_keypair_gen(codename)

        # Create 2 replies to test deleting on journalist and source interface
        for i in range(2):
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

        _block_on_reply_keypair_gen(codename)

        # Test deleting reply on the journalist interface
        soup = BeautifulSoup(rv.data)
        last_reply_number = len(soup.select('input[name="doc_names_selected"]')) - 1
        self.helper_filenames_delete(soup, last_reply_number)

        with self.source_app as source_app:
            rv = source_app.post('/login', data=dict(codename=codename),
                                 follow_redirects=True)
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
                    msgid=msgid
                ), follow_redirects=True)
                self.assertEqual(rv.status_code, 200)
                self.assertIn("Reply deleted", rv.data)
                common.logout(source_app)

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
        rv = self.journalist_app.post('/col/delete/' + sid,
                                      follow_redirects=True)
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
                msg="This is a test " + str(i) + ".",
                fh=(StringIO(''), ''),
            ), follow_redirects=True)
            common.logout(self.source_app)

        rv = self.journalist_app.get('/')
        # get all the checkbox values
        soup = BeautifulSoup(rv.data)
        checkbox_values = [checkbox['value'] for checkbox in
                           soup.select('input[name="cols_selected"]')]
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
        for i, submission_link in enumerate(soup.select('ul#submissions li a .filename')):
            filename = str(submission_link.contents[0])
            self.assertTrue(re.match(submission_filename_re.format(i + 1),
                                     filename))

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
        filename = str(soup.select('ul#submissions li a .filename')[0].contents[0])
        self.assertTrue(re.match(submission_filename_re.format(1), filename))
        filename = str(soup.select('ul#submissions li a .filename')[1].contents[0])
        self.assertTrue(re.match(submission_filename_re.format(3), filename))
        filename = str(soup.select('ul#submissions li a .filename')[2].contents[0])
        self.assertTrue(re.match(submission_filename_re.format(4), filename))

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

if __name__ == "__main__":
    unittest.main(verbosity=2)
