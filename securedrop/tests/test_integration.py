# -*- coding: utf-8 -*-
from cStringIO import StringIO
import gzip
import mock
import os
import re
import shutil
import tempfile
import unittest
import zipfile

from bs4 import BeautifulSoup
from flask import session, g, escape
from mock import patch
import gnupg

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
import config
import crypto_util
from db import db_session, Journalist
import journalist
import source
import store
import utils


class TestIntegration(unittest.TestCase):

    def _login_user(self):
        self.journalist_app.post('/login', data=dict(
            username=self.user.username,
            password=self.user_pw,
            token='mocked'),
            follow_redirects=True)

    def setUp(self):
        utils.env.setup()

        self.source_app = source.app.test_client()
        self.journalist_app = journalist.app.test_client()

        self.gpg = gnupg.GPG(homedir=config.GPG_KEY_DIR)

        # Patch the two-factor verification to avoid intermittent errors
        patcher = mock.patch('db.Journalist.verify_token')
        self.addCleanup(patcher.stop)
        self.mock_journalist_verify_token = patcher.start()
        self.mock_journalist_verify_token.return_value = True

        # Add a test user to the journalist interface and log them in
        # print Journalist.query.all()
        self.user_pw = "corret horse battery staple haha cultural reference"
        self.user = Journalist(username="some-username",
                               password=self.user_pw)
        db_session.add(self.user)
        db_session.commit()
        self._login_user()

    def tearDown(self):
        utils.env.teardown()

    def test_submit_message(self):
        """When a source creates an account, test that a new entry appears
        in the journalist interface"""
        test_msg = "This is a test message."

        with self.source_app as source_app:
            resp = source_app.get('/generate')
            resp = source_app.post('/create', follow_redirects=True)
            filesystem_id = g.filesystem_id
            # redirected to submission form
            resp = self.source_app.post('/submit', data=dict(
                msg=test_msg,
                fh=(StringIO(''), ''),
            ), follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            source_app.get('/logout')

        # Request the Journalist Interface index
        rv = self.journalist_app.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Sources", rv.data)
        soup = BeautifulSoup(rv.data, 'html.parser')

        # The source should have a "download unread" link that says "1 unread"
        col = soup.select('ul#cols > li')[0]
        unread_span = col.select('span.unread a')[0]
        self.assertIn("1 unread", unread_span.get_text())

        col_url = soup.select('ul#cols > li a')[0]['href']
        resp = self.journalist_app.get(col_url)
        self.assertEqual(resp.status_code, 200)
        soup = BeautifulSoup(resp.data, 'html.parser')
        submission_url = soup.select('ul#submissions li a')[0]['href']
        self.assertIn("-msg", submission_url)
        span = soup.select('ul#submissions li span.info span')[0]
        self.assertRegexpMatches(span['title'], "\d+ bytes")

        resp = self.journalist_app.get(submission_url)
        self.assertEqual(resp.status_code, 200)
        decrypted_data = self.gpg.decrypt(resp.data)
        self.assertTrue(decrypted_data.ok)
        self.assertEqual(decrypted_data.data, test_msg)

        # delete submission
        resp = self.journalist_app.get(col_url)
        self.assertEqual(resp.status_code, 200)
        soup = BeautifulSoup(resp.data, 'html.parser')
        doc_name = soup.select(
            'ul > li > input[name="doc_names_selected"]')[0]['value']
        resp = self.journalist_app.post('/bulk', data=dict(
            action='confirm_delete',
            filesystem_id=filesystem_id,
            doc_names_selected=doc_name
        ))

        self.assertEqual(resp.status_code, 200)
        soup = BeautifulSoup(resp.data, 'html.parser')
        self.assertIn("The following file has been selected for", resp.data)

        # confirm delete submission
        doc_name = soup.select
        doc_name = soup.select(
            'ul > li > input[name="doc_names_selected"]')[0]['value']
        resp = self.journalist_app.post('/bulk', data=dict(
            action='delete',
            filesystem_id=filesystem_id,
            doc_names_selected=doc_name,
        ), follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        soup = BeautifulSoup(resp.data, 'html.parser')
        self.assertIn("Submission deleted.", resp.data)

        # confirm that submission deleted and absent in list of submissions
        resp = self.journalist_app.get(col_url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("No documents to display.", resp.data)

        # the file should be deleted from the filesystem
        # since file deletion is handled by a polling worker, this test needs
        # to wait for the worker to get the job and execute it
        utils.async.wait_for_assertion(
            lambda: self.assertFalse(
                os.path.exists(store.path(filesystem_id, doc_name))
            )
        )

    def test_submit_file(self):
        """When a source creates an account, test that a new entry appears
        in the journalist interface"""
        test_file_contents = "This is a test file."
        test_filename = "test.txt"

        with self.source_app as source_app:
            resp = source_app.get('/generate')
            resp = source_app.post('/create', follow_redirects=True)
            filesystem_id = g.filesystem_id
            # redirected to submission form
            resp = self.source_app.post('/submit', data=dict(
                msg="",
                fh=(StringIO(test_file_contents), test_filename),
            ), follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            source_app.get('/logout')

        resp = self.journalist_app.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Sources", resp.data)
        soup = BeautifulSoup(resp.data, 'html.parser')

        # The source should have a "download unread" link that says "1 unread"
        col = soup.select('ul#cols > li')[0]
        unread_span = col.select('span.unread a')[0]
        self.assertIn("1 unread", unread_span.get_text())

        col_url = soup.select('ul#cols > li a')[0]['href']
        resp = self.journalist_app.get(col_url)
        self.assertEqual(resp.status_code, 200)
        soup = BeautifulSoup(resp.data, 'html.parser')
        submission_url = soup.select('ul#submissions li a')[0]['href']
        self.assertIn("-doc", submission_url)
        span = soup.select('ul#submissions li span.info span')[0]
        self.assertRegexpMatches(span['title'], "\d+ bytes")

        resp = self.journalist_app.get(submission_url)
        self.assertEqual(resp.status_code, 200)
        decrypted_data = self.gpg.decrypt(resp.data)
        self.assertTrue(decrypted_data.ok)

        sio = StringIO(decrypted_data.data)
        with gzip.GzipFile(mode='rb', fileobj=sio) as gzip_file:
            unzipped_decrypted_data = gzip_file.read()
        self.assertEqual(unzipped_decrypted_data, test_file_contents)

        # delete submission
        resp = self.journalist_app.get(col_url)
        self.assertEqual(resp.status_code, 200)
        soup = BeautifulSoup(resp.data, 'html.parser')
        doc_name = soup.select(
            'ul > li > input[name="doc_names_selected"]')[0]['value']
        resp = self.journalist_app.post('/bulk', data=dict(
            action='confirm_delete',
            filesystem_id=filesystem_id,
            doc_names_selected=doc_name
        ))

        self.assertEqual(resp.status_code, 200)
        soup = BeautifulSoup(resp.data, 'html.parser')
        self.assertIn("The following file has been selected for", resp.data)

        # confirm delete submission
        doc_name = soup.select
        doc_name = soup.select(
            'ul > li > input[name="doc_names_selected"]')[0]['value']
        resp = self.journalist_app.post('/bulk', data=dict(
            action='delete',
            filesystem_id=filesystem_id,
            doc_names_selected=doc_name,
        ), follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        soup = BeautifulSoup(resp.data, 'html.parser')
        self.assertIn("Submission deleted.", resp.data)

        # confirm that submission deleted and absent in list of submissions
        resp = self.journalist_app.get(col_url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("No documents to display.", resp.data)

        # the file should be deleted from the filesystem
        # since file deletion is handled by a polling worker, this test needs
        # to wait for the worker to get the job and execute it
        utils.async.wait_for_assertion(
            lambda: self.assertFalse(
                os.path.exists(store.path(filesystem_id, doc_name))
            )
        )

    def test_reply_normal(self):
        self.helper_test_reply("This is a test reply.", True)

    def test_unicode_reply_with_ansi_env(self):
        # This makes python-gnupg handle encoding equivalent to if we were
        # running SD in an environment where os.getenv("LANG") == "C".
        # Unfortunately, with the way our test suite is set up simply setting
        # that env var here will not have the desired effect. Instead we
        # monkey-patch the GPG object that is called crypto_util to imitate the
        # _encoding attribute it would have had it been initialized in a "C"
        # environment. See
        # https://github.com/freedomofpress/securedrop/issues/1360 for context.
        old_encoding = crypto_util.gpg._encoding
        crypto_util.gpg._encoding = "ansi_x3.4_1968"
        try:
            self.helper_test_reply("ᚠᛇᚻ᛫ᛒᛦᚦ᛫ᚠᚱᚩᚠᚢᚱ᛫ᚠᛁᚱᚪ᛫ᚷᛖᚻᚹᛦᛚᚳᚢᛗ", True)
        finally:
            crypto_util.gpg._encoding = old_encoding

    def _can_decrypt_with_key(self, msg, key_fpr, passphrase=None):
        """
        Test that the given GPG message can be decrypted with the given key
        (identified by its fingerprint).
        """
        # GPG does not provide a way to specify which key to use to decrypt a
        # message. Since the default keyring that we use has both the
        # `config.JOURNALIST_KEY` and all of the reply keypairs, there's no way
        # to use it to test whether a message is decryptable with a specific
        # key.
        gpg_tmp_dir = tempfile.mkdtemp()
        gpg = gnupg.GPG(homedir=gpg_tmp_dir)

        # Export the key of interest from the application's keyring
        pubkey = self.gpg.export_keys(key_fpr)
        seckey = self.gpg.export_keys(key_fpr, secret=True)
        # Import it into our isolated temporary GPG directory
        for key in (pubkey, seckey):
            gpg.import_keys(key)

        # Attempt decryption with the given key
        if passphrase:
            passphrase = crypto_util.hash_codename(
                passphrase,
                salt=crypto_util.SCRYPT_GPG_PEPPER)
        decrypted_data = gpg.decrypt(msg, passphrase=passphrase)
        self.assertTrue(
            decrypted_data.ok,
            "Could not decrypt msg with key, gpg says: {}".format(
                decrypted_data.stderr))

        # We have to clean up the temporary GPG dir
        shutil.rmtree(gpg_tmp_dir)

    def helper_test_reply(self, test_reply, expected_success=True):
        test_msg = "This is a test message."

        with self.source_app as source_app:
            resp = source_app.get('/generate')
            resp = source_app.post('/create', follow_redirects=True)
            codename = session['codename']
            filesystem_id = g.filesystem_id
            # redirected to submission form
            resp = source_app.post('/submit', data=dict(
                msg=test_msg,
                fh=(StringIO(''), ''),
            ), follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertFalse(g.source.flagged)
            source_app.get('/logout')

        resp = self.journalist_app.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Sources", resp.data)
        soup = BeautifulSoup(resp.data, 'html.parser')
        col_url = soup.select('ul#cols > li a')[0]['href']

        resp = self.journalist_app.get(col_url)
        self.assertEqual(resp.status_code, 200)

        with self.source_app as source_app:
            resp = source_app.post('/login', data=dict(
                codename=codename), follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertFalse(g.source.flagged)
            source_app.get('/logout')

        with self.journalist_app as journalist_app:
            resp = journalist_app.post('/flag', data=dict(
                filesystem_id=filesystem_id))
            self.assertEqual(resp.status_code, 200)

        with self.source_app as source_app:
            resp = source_app.post('/login', data=dict(
                codename=codename), follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(g.source.flagged)
            source_app.get('/lookup')
            self.assertTrue(g.source.flagged)
            source_app.get('/logout')

        # Block up to 15s for the reply keypair, so we can test sending a reply
        utils.async.wait_for_assertion(
            lambda: self.assertNotEqual(crypto_util.getkey(filesystem_id),
                                        None),
            15)

        # Create 2 replies to test deleting on journalist and source interface
        for i in range(2):
            resp = self.journalist_app.post('/reply', data=dict(
                filesystem_id=filesystem_id,
                message=test_reply
            ), follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

        if not expected_success:
            pass
        else:
            self.assertIn("Thanks. Your reply has been stored.", resp.data)

        with self.journalist_app as journalist_app:
            resp = journalist_app.get(col_url)
            self.assertIn("reply-", resp.data)

        soup = BeautifulSoup(resp.data, 'html.parser')

        # Download the reply and verify that it can be decrypted with the
        # journalist's key as well as the source's reply key
        filesystem_id = soup.select('input[name="filesystem_id"]')[0]['value']
        checkbox_values = [
            soup.select('input[name="doc_names_selected"]')[1]['value']]
        resp = self.journalist_app.post('/bulk', data=dict(
            filesystem_id=filesystem_id,
            action='download',
            doc_names_selected=checkbox_values
        ), follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        zf = zipfile.ZipFile(StringIO(resp.data), 'r')
        data = zf.read(zf.namelist()[0])
        self._can_decrypt_with_key(data, config.JOURNALIST_KEY)
        self._can_decrypt_with_key(data, crypto_util.getkey(filesystem_id),
                                   codename)

        # Test deleting reply on the journalist interface
        last_reply_number = len(
            soup.select('input[name="doc_names_selected"]')) - 1
        self.helper_filenames_delete(soup, last_reply_number)

        with self.source_app as source_app:
            resp = source_app.post('/login', data=dict(codename=codename),
                                   follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            resp = source_app.get('/lookup')
            self.assertEqual(resp.status_code, 200)

            if not expected_success:
                # there should be no reply
                self.assertNotIn("You have received a reply.", resp.data)
            else:
                self.assertIn(
                    "You have received a reply. To protect your identity",
                    resp.data)
                self.assertIn(test_reply, resp.data)
                soup = BeautifulSoup(resp.data, 'html.parser')
                msgid = soup.select(
                    'form.message > input[name="reply_filename"]')[0]['value']
                resp = source_app.post('/delete', data=dict(
                    filesystem_id=filesystem_id,
                    reply_filename=msgid
                ), follow_redirects=True)
                self.assertEqual(resp.status_code, 200)
                self.assertIn("Reply deleted", resp.data)

                # Make sure the reply is deleted from the filesystem
                utils.async.wait_for_assertion(
                    lambda: self.assertFalse(os.path.exists(
                        store.path(filesystem_id, msgid))))

            source_app.get('/logout')

    @patch('source_app.main.async_genkey')
    def test_delete_collection(self, async_genkey):
        """Test the "delete collection" button on each collection page"""
        # first, add a source
        self.source_app.get('/generate')
        self.source_app.post('/create')
        resp = self.source_app.post('/submit', data=dict(
            msg="This is a test.",
            fh=(StringIO(''), ''),
        ), follow_redirects=True)

        assert resp.status_code == 200, resp.data.decode('utf-8')

        resp = self.journalist_app.get('/')
        # navigate to the collection page
        soup = BeautifulSoup(resp.data, 'html.parser')
        first_col_url = soup.select('ul#cols > li a')[0]['href']
        resp = self.journalist_app.get(first_col_url)
        self.assertEqual(resp.status_code, 200)

        # find the delete form and extract the post parameters
        soup = BeautifulSoup(resp.data, 'html.parser')
        delete_form_inputs = soup.select('form#delete-collection')[0]('input')
        filesystem_id = delete_form_inputs[1]['value']
        col_name = delete_form_inputs[2]['value']

        resp = self.journalist_app.post('/col/delete/' + filesystem_id,
                                        follow_redirects=True)
        self.assertEquals(resp.status_code, 200)

        self.assertIn(escape("%s's collection deleted" % (col_name,)),
                      resp.data)
        self.assertIn("No documents have been submitted!", resp.data)
        self.assertTrue(async_genkey.called)

        # Make sure the collection is deleted from the filesystem
        utils.async.wait_for_assertion(
            lambda: self.assertFalse(os.path.exists(store.path(filesystem_id)))
        )

    @patch('source_app.main.async_genkey')
    def test_delete_collections(self, async_genkey):
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
            self.source_app.get('/logout')

        resp = self.journalist_app.get('/')
        # get all the checkbox values
        soup = BeautifulSoup(resp.data, 'html.parser')
        checkbox_values = [checkbox['value'] for checkbox in
                           soup.select('input[name="cols_selected"]')]

        resp = self.journalist_app.post('/col/process', data=dict(
            action='delete',
            cols_selected=checkbox_values
        ), follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("%s collections deleted" % (num_sources,), resp.data)
        self.assertTrue(async_genkey.called)

        # Make sure the collections are deleted from the filesystem
        utils.async.wait_for_assertion(lambda: self.assertFalse(
            any([os.path.exists(store.path(filesystem_id))
                for filesystem_id in checkbox_values])))

    def test_filenames(self):
        """Test pretty, sequential filenames when source uploads messages
        and files"""
        # add a source and submit stuff
        self.source_app.get('/generate')
        self.source_app.post('/create')
        self.helper_filenames_submit()

        # navigate to the collection page
        resp = self.journalist_app.get('/')
        soup = BeautifulSoup(resp.data, 'html.parser')
        first_col_url = soup.select('ul#cols > li a')[0]['href']
        resp = self.journalist_app.get(first_col_url)
        self.assertEqual(resp.status_code, 200)

        # test filenames and sort order
        soup = BeautifulSoup(resp.data, 'html.parser')
        submission_filename_re = r'^{0}-[a-z0-9-_]+(-msg|-doc\.gz)\.gpg$'
        for i, submission_link in enumerate(
                soup.select('ul#submissions li a .filename')):
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
        resp = self.journalist_app.get('/')
        soup = BeautifulSoup(resp.data, 'html.parser')
        first_col_url = soup.select('ul#cols > li a')[0]['href']
        resp = self.journalist_app.get(first_col_url)
        self.assertEqual(resp.status_code, 200)
        soup = BeautifulSoup(resp.data, 'html.parser')

        # delete file #2
        self.helper_filenames_delete(soup, 1)
        resp = self.journalist_app.get(first_col_url)
        soup = BeautifulSoup(resp.data, 'html.parser')

        # test filenames and sort order
        submission_filename_re = r'^{0}-[a-z0-9-_]+(-msg|-doc\.gz)\.gpg$'
        filename = str(
            soup.select('ul#submissions li a .filename')[0].contents[0])
        self.assertTrue(re.match(submission_filename_re.format(1), filename))
        filename = str(
            soup.select('ul#submissions li a .filename')[1].contents[0])
        self.assertTrue(re.match(submission_filename_re.format(3), filename))
        filename = str(
            soup.select('ul#submissions li a .filename')[2].contents[0])
        self.assertTrue(re.match(submission_filename_re.format(4), filename))

    def test_user_change_password(self):
        """Test that a journalist can successfully login after changing
        their password"""

        # change password
        new_pw = 'another correct horse battery staply long password'
        self.journalist_app.post('/account/new-password',
                                 data=dict(password=new_pw,
                                           current_password=self.user_pw,
                                           token='mocked'))

        # logout
        self.journalist_app.get('/logout')

        # login with new credentials should redirect to index page
        resp = self.journalist_app.post('/login', data=dict(
            username=self.user.username,
            password=new_pw,
            token='mocked',
            follow_redirects=True))
        self.assertEqual(resp.status_code, 302)

    def test_login_after_regenerate_hotp(self):
        """Test that journalists can login after resetting their HOTP 2fa"""

        # edit hotp
        self.journalist_app.post('/account/reset-2fa-hotp', data=dict(
            otp_secret=123456))

        # successful verificaton should redirect to /account
        resp = self.journalist_app.post('/account/2fa', data=dict(
            token=self.user.hotp))
        self.assertEqual(resp.status_code, 302)

        # log out
        self.journalist_app.get('/logout')

        # login with new 2fa secret should redirect to index page
        resp = self.journalist_app.post('/login', data=dict(
            username=self.user.username,
            password=self.user_pw,
            token=self.user.hotp,
            follow_redirects=True))
        self.assertEqual(resp.status_code, 302)

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
        filesystem_id = soup.select('input[name="filesystem_id"]')[0]['value']
        checkbox_values = [
            soup.select('input[name="doc_names_selected"]')[i]['value']]

        # delete
        resp = self.journalist_app.post('/bulk', data=dict(
            filesystem_id=filesystem_id,
            action='confirm_delete',
            doc_names_selected=checkbox_values
        ), follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(
            "The following file has been selected for"
            " <strong>permanent deletion</strong>",
            resp.data)

        # confirm delete
        resp = self.journalist_app.post('/bulk', data=dict(
            filesystem_id=filesystem_id,
            action='delete',
            doc_names_selected=checkbox_values
        ), follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Submission deleted.", resp.data)

        # Make sure the files were deleted from the filesystem
        utils.async.wait_for_assertion(lambda: self.assertFalse(
            any([os.path.exists(store.path(filesystem_id, doc_name))
                 for doc_name in checkbox_values])))
