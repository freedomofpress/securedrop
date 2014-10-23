#!/usr/bin/env python
# -*- coding: utf-8 -*-
import common
import os
import re
import unittest
from cStringIO import StringIO

from bs4 import BeautifulSoup
from flask.ext.testing import TestCase
from flask import session, escape
from mock import patch, ANY

os.environ['SECUREDROP_ENV'] = 'test'
import source


class TestSource(TestCase):

    def create_app(self):
        return source.app

    def setUp(self):
        common.shared_setup()

    def tearDown(self):
        common.shared_teardown()

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
            rv = c.get('/generate')
            self.assertEqual(rv.status_code, 200)
            session_codename = session['codename']
        self.assertIn("Remember this code and keep it secret", rv.data)
        self.assertIn(
            "To protect your identity, we're assigning you a unique codename.",
            rv.data)
        codename = self._find_codename(rv.data)
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
            self.assertIn("Submit documents and messages", rv.data)

    def _new_codename(self):
        return common.new_codename(self.client, session)

    def test_lookup(self):
        """Test various elements on the /lookup page"""
        codename = self._new_codename()
        rv = self.client.post('login', data=dict(codename=codename),
                              follow_redirects=True)
        # redirects to /lookup
        self.assertIn("public key", rv.data)
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
            self.assertIn("Submit documents and messages", rv.data)
            self.assertTrue(session['logged_in'])
            common.logout(c)

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
        self.assertIn(escape('{} "{}"'.format("Thanks! We received your document", "test.txt")), rv.data)

    def test_submit_both(self):
        self._new_codename()
        rv = self.client.post('/submit', data=dict(
            msg="This is a test",
            fh=(StringIO('This is a test'), 'test.txt'),
        ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn("Thanks! We received your message.", rv.data)
        self.assertIn(escape('{} "{}"'.format("Thanks! We received your document", 'test.txt')), rv.data)

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
