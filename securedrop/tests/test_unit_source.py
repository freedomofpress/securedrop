#!/usr/bin/env python
# -*- coding: utf-8 -*-
from cStringIO import StringIO
from mock import patch, ANY
import os
import re
import unittest

from bs4 import BeautifulSoup
from flask import session, escape
from flask_testing import TestCase

from db import Source
import source
import utils


class TestSourceApppp(TestCase):

    def create_app(self):
        return source.app

    def setUp(self):
        utils.env.setup()

    def tearDown(self):
        utils.env.teardown()

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
        codename_re = r'<p id="codename">(?P<codename>[a-z0-9 &#;?:=@_.*+()\'"$%!-]+)</p>'
        codename_match = re.search(codename_re, html)
        self.assertIsNotNone(codename_match)
        return codename_match.group('codename')

    def test_generate(self):
        with self.client as c:
            resp = c.get('/generate')
            self.assertEqual(resp.status_code, 200)
            session_codename = session['codename']
        self.assertIn("Remember this codename and keep it secret", resp.data)
        self.assertIn(
            "To protect your identity, we're assigning you a unique codename.",
            resp.data)
        codename = self._find_codename(resp.data)
        # default codename length is 7 words
        self.assertEqual(len(codename.split()), 7)
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
        """The generate page should have a link to remind people to login
           if they already have a codename, rather than create a new one.
        """
        resp = self.client.get('/generate')
        self.assertIn("Already have a codename?", resp.data)
        soup = BeautifulSoup(resp.data)
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
            self.assertIn("Submit documents and messages", resp.data)

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
        self.assertIn("Login to check for responses", resp.data)

        codename = self._new_codename()
        with self.client as c:
            resp = c.post('/login', data=dict(codename=codename),
                          follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Submit documents and messages", resp.data)
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
            self.assertIn('Thank you for logging out.', resp.data)

    def test_login_with_whitespace(self):
        """Test that codenames with leading or trailing whitespace still work"""
        def login_test(codename):
            resp = self.client.get('/login')
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Login to check for responses", resp.data)

            with self.client as c:
                resp = c.post('/login', data=dict(codename=codename),
                            follow_redirects=True)
                self.assertEqual(resp.status_code, 200)
                self.assertIn("Submit documents and messages", resp.data)
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
            "Thanks for submitting something to SecureDrop! Please check back later for replies.",
            resp.data)

    def test_submit_message(self):
        self._new_codename()
        self._dummy_submission()
        resp = self.client.post('/submit', data=dict(
            msg="This is a test.",
            fh=(StringIO(''), ''),
        ), follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Thanks! We received your message.", resp.data)

    def test_submit_empty_message(self):
        self._new_codename()
        resp = self.client.post('/submit', data=dict(
            msg="",
            fh=(StringIO(''), ''),
        ), follow_redirects=True)
        self.assertIn("You must enter a message or choose a file to submit.", resp.data)

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
        self.assertIn("Thanks! We received your message.", resp.data)

    def test_submit_file(self):
        self._new_codename()
        self._dummy_submission()
        resp = self.client.post('/submit', data=dict(
            msg="",
            fh=(StringIO('This is a test'), 'test.txt'),
        ), follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(
            escape(
                '{} "{}"'.format(
                    "Thanks! We received your document",
                    "test.txt")),
            resp.data)

    def test_submit_both(self):
        self._new_codename()
        self._dummy_submission()
        resp = self.client.post('/submit', data=dict(
            msg="This is a test",
            fh=(StringIO('This is a test'), 'test.txt'),
        ), follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Thanks! We received your message.", resp.data)
        self.assertIn(
            escape(
                '{} "{}"'.format(
                    "Thanks! We received your document",
                    'test.txt')),
            resp.data)

    @patch('gzip.GzipFile')
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

    def test_tor2web_warning_headers(self):
        resp = self.client.get('/', headers=[('X-tor2web', 'encrypted')])
        self.assertEqual(resp.status_code, 200)
        self.assertIn("You appear to be using Tor2Web.", resp.data)

    def test_tor2web_warning(self):
        resp = self.client.get('/tor2web-warning')
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Why is there a warning about Tor2Web?", resp.data)

    def test_why_journalist_key(self):
        resp = self.client.get('/why-journalist-key')
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Why download the journalist's public key?", resp.data)

    def test_howto_disable_js(self):
        resp = self.client.get('/howto-disable-js')
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Turn the Security Slider to High to Protect Your "
                      "Anonymity", resp.data)

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
