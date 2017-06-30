# -*- coding: utf-8 -*-
from cStringIO import StringIO
import gzip
from mock import patch, ANY
import os
import re
import unittest

from bs4 import BeautifulSoup
from flask import session, escape
from flask_testing import TestCase

from db import Source
import source
import version
import utils
import json
import config


class TestSourceApp(TestCase):

    def create_app(self):
        return source.app

    def setUp(self):
        utils.env.setup()

    def tearDown(self):
        utils.env.teardown()

    def test_page_not_found(self):
        """Verify the page not found condition returns the intended template"""
        response = self.client.get('/UNKNOWN')
        self.assert404(response)
        self.assertTemplateUsed('notfound.html')

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
        codename_re = r'<p [^>]*id="codename"[^>]*>(?P<codename>[a-z0-9 &#;?:=@_.*+()\'"$%!-]+)</p>'
        codename_match = re.search(codename_re, html)
        self.assertIsNotNone(codename_match)
        return codename_match.group('codename')

    def test_generate(self):
        with self.client as c:
            resp = c.get('/generate')
            self.assertEqual(resp.status_code, 200)
            session_codename = session['codename']
        self.assertIn("This codename is what you will use in future visits", resp.data)
        codename = self._find_codename(resp.data)
        self.assertEqual(len(codename.split()), Source.NUM_WORDS)
        # codename is also stored in the session - make sure it matches the
        # codename displayed to the source
        self.assertEqual(codename, escape(session_codename))

    def test_generate_has_login_link(self):
        """The generate page should have a link to remind people to login
           if they already have a codename, rather than create a new one.
        """
        resp = self.client.get('/generate')
        self.assertIn("ALREADY HAVE A CODENAME?", resp.data)
        soup = BeautifulSoup(resp.data, 'html5lib')
        already_have_codename_link = soup.select('a#already-have-codename')[0]
        self.assertEqual(already_have_codename_link['href'], '/login')

    def test_generate_already_logged_in(self):
        self._new_codename()
        # Make sure it redirects to /lookup when logged in
        resp = self.client.get('/generate')
        self.assertEqual(resp.status_code, 302)
        # Make sure it flashes the message on the lookup page
        resp = self.client.get('/generate', follow_redirects=True)
        # Should redirect to /lookup
        self.assertEqual(resp.status_code, 200)
        self.assertIn("because you are already logged in.", resp.data)

    def test_create(self):
        with self.client as c:
            resp = c.get('/generate')
            codename = session['codename']
            resp = c.post('/create', follow_redirects=True)
            self.assertTrue(session['logged_in'])
            # should be redirected to /lookup
            self.assertIn("Submit Materials", resp.data)

    def _new_codename(self):
        return utils.db_helper.new_codename(self.client, session)

    def test_lookup(self):
        """Test various elements on the /lookup page."""
        codename = self._new_codename()
        resp = self.client.post('login', data=dict(codename=codename),
                                follow_redirects=True)
        # redirects to /lookup
        self.assertIn("public key", resp.data)
        # download the public key
        resp = self.client.get('journalist-key')
        self.assertIn("BEGIN PGP PUBLIC KEY BLOCK", resp.data)

    def test_login_and_logout(self):
        resp = self.client.get('/login')
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Enter Codename", resp.data)

        codename = self._new_codename()
        with self.client as c:
            resp = c.post('/login', data=dict(codename=codename),
                          follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Submit Materials", resp.data)
            self.assertTrue(session['logged_in'])
            resp = c.get('/logout', follow_redirects=True)

        with self.client as c:
            resp = c.post('/login', data=dict(codename='invalid'),
                                  follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Sorry, that is not a recognized codename.', resp.data)
            self.assertNotIn('logged_in', session)

        with self.client as c:
            resp = c.post('/login', data=dict(codename=codename),
                        follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(session['logged_in'])
            resp = c.get('/logout', follow_redirects=True)
            self.assertTrue(not session)
            self.assertIn('Thank you for exiting your session!', resp.data)

    def test_login_with_whitespace(self):
        """Test that codenames with leading or trailing whitespace still work"""
        def login_test(codename):
            resp = self.client.get('/login')
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Enter Codename", resp.data)

            with self.client as c:
                resp = c.post('/login', data=dict(codename=codename),
                            follow_redirects=True)
                self.assertEqual(resp.status_code, 200)
                self.assertIn("Submit Materials", resp.data)
                self.assertTrue(session['logged_in'])
                resp = c.get('/logout', follow_redirects=True)

        codename = self._new_codename()
        login_test(codename + ' ')
        login_test(' ' + codename + ' ')
        login_test(' ' + codename)

    def _dummy_submission(self):
        """
        Helper to make a submission (content unimportant), mostly useful in
        testing notification behavior for a source's first vs. their
        subsequent submissions
        """
        return self.client.post('/submit', data=dict(
            msg="Pay no attention to the man behind the curtain.",
            fh=(StringIO(''), ''),
        ), follow_redirects=True)

    def test_initial_submission_notification(self):
        """
        Regardless of the type of submission (message, file, or both), the
        first submission is always greeted with a notification
        reminding sources to check back later for replies.
        """
        self._new_codename()
        resp = self._dummy_submission()
        self.assertEqual(resp.status_code, 200)
        self.assertIn(
            "Thank you for sending this information to us.",
            resp.data)

    def test_submit_message(self):
        self._new_codename()
        self._dummy_submission()
        resp = self.client.post('/submit', data=dict(
            msg="This is a test.",
            fh=(StringIO(''), ''),
        ), follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Thanks! We received your message", resp.data)

    def test_submit_empty_message(self):
        self._new_codename()
        resp = self.client.post('/submit', data=dict(
            msg="",
            fh=(StringIO(''), ''),
        ), follow_redirects=True)
        self.assertIn("You must enter a message or choose a file to submit.",
                      resp.data)

    def test_submit_big_message(self):
        '''
        When the message is larger than 512KB it's written to disk instead of
        just residing in memory. Make sure the different return type of
        SecureTemporaryFile is handled as well as BytesIO.
        '''
        self._new_codename()
        self._dummy_submission()
        resp = self.client.post('/submit', data=dict(
            msg="AA" * (1024 * 512),
            fh=(StringIO(''), ''),
        ), follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Thanks! We received your message", resp.data)

    def test_submit_file(self):
        self._new_codename()
        self._dummy_submission()
        resp = self.client.post('/submit', data=dict(
            msg="",
            fh=(StringIO('This is a test'), 'test.txt'),
        ), follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Thanks! We received your document', resp.data)

    def test_submit_both(self):
        self._new_codename()
        self._dummy_submission()
        resp = self.client.post('/submit', data=dict(
            msg="This is a test",
            fh=(StringIO('This is a test'), 'test.txt'),
        ), follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Thanks! We received your message and document",
                      resp.data)

    def test_delete_all(self):
        journalist, _ = utils.db_helper.init_journalist()
        source, codename = utils.db_helper.init_source()
        replies = utils.db_helper.reply(journalist, source, 1)
        with self.client as c:
            resp = c.post('/login', data=dict(codename=codename),
                          follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            resp = c.post('/delete-all', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("All replies have been deleted", resp.data)

    @patch('gzip.GzipFile', wraps=gzip.GzipFile)
    def test_submit_sanitizes_filename(self, gzipfile):
        """Test that upload file name is sanitized"""
        insecure_filename = '../../bin/gpg'
        sanitized_filename = 'bin_gpg'

        self._new_codename()
        self.client.post('/submit', data=dict(
            msg="",
            fh=(StringIO('This is a test'), insecure_filename),
        ), follow_redirects=True)
        gzipfile.assert_called_with(filename=sanitized_filename,
                                    mode=ANY,
                                    fileobj=ANY)

    def test_custom_notification(self):
        """Test that `CUSTOM_NOTIFICATION` string in config file
        is rendered on the Source Interface page. We cannot assume
        it will be present in production instances, since it is added
        via the Ansible config, not the Debian package scripts."""
        custom_msg = config.CUSTOM_NOTIFICATION

        dev_msg = ("This is an insecure SecureDrop Development server "
                   "for testing ONLY. Do NOT submit documents here.")
        staging_msg = "This is a SecureDrop Staging VM for testing ONLY"

        self.assertTrue(custom_msg in (dev_msg, staging_msg))
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        # The app-tests aren't host-aware, so we can't accurately predict
        # which custom notification message we want. Let's check for both,
        # and fail only if both are not found.
        try:
            self.assertIn(dev_msg, resp.data)
        except AssertionError:
            self.assertIn(staging_msg, resp.data)

    def test_tor2web_warning_headers(self):
        resp = self.client.get('/', headers=[('X-tor2web', 'encrypted')])
        self.assertEqual(resp.status_code, 200)
        self.assertIn("You appear to be using Tor2Web.", resp.data)

    def test_tor2web_warning(self):
        resp = self.client.get('/tor2web-warning')
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Why is there a warning about Tor2Web?", resp.data)

    def test_why_use_tor_browser(self):
        resp = self.client.get('/use-tor')
        self.assertEqual(resp.status_code, 200)
        self.assertIn("You Should Use Tor Browser", resp.data)

    def test_why_journalist_key(self):
        resp = self.client.get('/why-journalist-key')
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Why download the journalist's public key?", resp.data)

    def test_metadata_route(self):
        resp = self.client.get('/metadata')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get('Content-Type'), 'application/json')
        self.assertEqual(json.loads(resp.data.decode('utf-8')).get('sd_version'), version.__version__)

    @patch('crypto_util.hash_codename')
    def test_login_with_overly_long_codename(self, mock_hash_codename):
        """Attempting to login with an overly long codename should result in
        an error, and scrypt should not be called to avoid DoS."""
        overly_long_codename = 'a' * (Source.MAX_CODENAME_LEN + 1)
        with self.client as c:
            resp = c.post('/login', data=dict(codename=overly_long_codename),
                          follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Sorry, that is not a recognized codename.", resp.data)
            self.assertFalse(mock_hash_codename.called,
                             "Called hash_codename for codename w/ invalid "
                             "length")
