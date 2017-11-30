# -*- coding: utf-8 -*-
from cStringIO import StringIO
import gzip
from mock import patch, ANY
import re

from bs4 import BeautifulSoup
from flask import session, escape, url_for
from flask_testing import TestCase

import crypto_util
from db import db_session, Source
import source
import version
import utils
import json
import config
from utils.db_helper import new_codename

overly_long_codename = 'a' * (Source.MAX_CODENAME_LEN + 1)


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

    def test_all_words_in_wordlist_validate(self):
        """Verify that all words in the wordlist are allowed by the form
        validation. Otherwise a source will have a codename and be unable to
        return."""

        wordlist_en = crypto_util._get_wordlist('en')

        # chunk the words to cut down on the number of requets we make
        # otherwise this test is *slow*
        chunks = [wordlist_en[i:i + 7] for i in range(0, len(wordlist_en), 7)]

        for words in chunks:
            with self.client as c:
                resp = c.post('/login', data=dict(codename=' '.join(words)),
                              follow_redirects=True)
                self.assertEqual(resp.status_code, 200)
                # If the word does not validate, then it will show
                # 'Invalid input'. If it does validate, it should show that
                # it isn't a recognized codename.
                self.assertIn('Sorry, that is not a recognized codename.',
                              resp.data)
                self.assertNotIn('logged_in', session)

    def _find_codename(self, html):
        """Find a source codename (diceware passphrase) in HTML"""
        # Codenames may contain HTML escape characters, and the wordlist
        # contains various symbols.
        codename_re = (r'<p [^>]*id="codename"[^>]*>'
                       r'(?P<codename>[a-z0-9 &#;?:=@_.*+()\'"$%!-]+)</p>')
        codename_match = re.search(codename_re, html)
        self.assertIsNotNone(codename_match)
        return codename_match.group('codename')

    def test_generate(self):
        with self.client as c:
            resp = c.get('/generate')
            self.assertEqual(resp.status_code, 200)
            session_codename = session['codename']
        self.assertIn("This codename is what you will use in future visits",
                      resp.data)
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
        self.assertIn("USE EXISTING CODENAME", resp.data)
        soup = BeautifulSoup(resp.data, 'html.parser')
        already_have_codename_link = soup.select('a#already-have-codename')[0]
        self.assertEqual(already_have_codename_link['href'], '/login')

    def test_generate_already_logged_in(self):
        with self.client as client:
            new_codename(client, session)
            # Make sure it redirects to /lookup when logged in
            resp = client.get('/generate')
            self.assertEqual(resp.status_code, 302)
            # Make sure it flashes the message on the lookup page
            resp = client.get('/generate', follow_redirects=True)
            # Should redirect to /lookup
            self.assertEqual(resp.status_code, 200)
            self.assertIn("because you are already logged in.", resp.data)

    def test_create_new_source(self):
        with self.client as c:
            resp = c.get('/generate')
            resp = c.post('/create', follow_redirects=True)
            self.assertTrue(session['logged_in'])
            # should be redirected to /lookup
            self.assertIn("Submit Materials", resp.data)

    @patch('source.app.logger.warning')
    @patch('crypto_util.genrandomid',
           side_effect=[overly_long_codename, 'short codename'])
    def test_generate_too_long_codename(self, genrandomid, logger):
        """Generate a codename that exceeds the maximum codename length"""

        with self.client as c:
            resp = c.post('/generate')
            self.assertEqual(resp.status_code, 200)

        logger.assert_called_with(
            "Generated a source codename that was too long, "
            "skipping it. This should not happen. "
            "(Codename='{}')".format(overly_long_codename)
        )

    @patch('source.app.logger.error')
    def test_create_duplicate_codename(self, logger):
        with self.client as c:
            c.get('/generate')

            # Create a source the first time
            c.post('/create', follow_redirects=True)

            # Attempt to add the same source
            c.post('/create', follow_redirects=True)
            logger.assert_called_once()
            self.assertIn("Attempt to create a source with duplicate codename",
                          logger.call_args[0][0])
            assert 'codename' not in session

    def test_lookup(self):
        """Test various elements on the /lookup page."""
        with self.client as client:
            codename = new_codename(client, session)
            resp = client.post('login', data=dict(codename=codename),
                               follow_redirects=True)
            # redirects to /lookup
            self.assertIn("public key", resp.data)
            # download the public key
            resp = client.get('journalist-key')
            self.assertIn("BEGIN PGP PUBLIC KEY BLOCK", resp.data)

    def test_login_and_logout(self):
        resp = self.client.get('/login')
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Enter Codename", resp.data)

        with self.client as client:
            codename = new_codename(client, session)
            resp = client.post('/login', data=dict(codename=codename),
                               follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Submit Materials", resp.data)
            self.assertTrue(session['logged_in'])
            resp = client.get('/logout', follow_redirects=True)

        with self.client as c:
            resp = c.post('/login', data=dict(codename='invalid'),
                          follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Sorry, that is not a recognized codename.',
                          resp.data)
            self.assertNotIn('logged_in', session)

        with self.client as c:
            resp = c.post('/login', data=dict(codename=codename),
                          follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(session['logged_in'])
            resp = c.get('/logout', follow_redirects=True)

            # sessions always have 'expires', so pop it for the next check
            session.pop('expires', None)

            self.assertNotIn('logged_in', session)
            self.assertNotIn('codename', session)

            self.assertIn('Thank you for exiting your session!', resp.data)

    def test_user_must_log_in_for_protected_views(self):
        with self.client as c:
            resp = c.get('/lookup', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Enter Codename", resp.data)

    def test_login_with_whitespace(self):
        """
        Test that codenames with leading or trailing whitespace still work"""

        with self.client as client:
            def login_test(codename):
                resp = client.get('/login')
                self.assertEqual(resp.status_code, 200)
                self.assertIn("Enter Codename", resp.data)

                resp = client.post('/login', data=dict(codename=codename),
                                   follow_redirects=True)
                self.assertEqual(resp.status_code, 200)
                self.assertIn("Submit Materials", resp.data)
                self.assertTrue(session['logged_in'])
                resp = client.get('/logout', follow_redirects=True)

            codename = new_codename(client, session)
            login_test(codename + ' ')
            login_test(' ' + codename + ' ')
            login_test(' ' + codename)

    def _dummy_submission(self, client):
        """
        Helper to make a submission (content unimportant), mostly useful in
        testing notification behavior for a source's first vs. their
        subsequent submissions
        """
        return client.post('/submit', data=dict(
            msg="Pay no attention to the man behind the curtain.",
            fh=(StringIO(''), ''),
        ), follow_redirects=True)

    def test_initial_submission_notification(self):
        """
        Regardless of the type of submission (message, file, or both), the
        first submission is always greeted with a notification
        reminding sources to check back later for replies.
        """
        with self.client as client:
            new_codename(client, session)
            resp = self._dummy_submission(client)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                "Thank you for sending this information to us.",
                resp.data)

    def test_submit_message(self):
        with self.client as client:
            new_codename(client, session)
            self._dummy_submission(client)
            resp = client.post('/submit', data=dict(
                msg="This is a test.",
                fh=(StringIO(''), ''),
            ), follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Thanks! We received your message", resp.data)

    def test_submit_empty_message(self):
        with self.client as client:
            new_codename(client, session)
            resp = client.post('/submit', data=dict(
                msg="",
                fh=(StringIO(''), ''),
            ), follow_redirects=True)
            self.assertIn("You must enter a message or choose a file to "
                          "submit.",
                          resp.data)

    def test_submit_big_message(self):
        '''
        When the message is larger than 512KB it's written to disk instead of
        just residing in memory. Make sure the different return type of
        SecureTemporaryFile is handled as well as BytesIO.
        '''
        with self.client as client:
            new_codename(client, session)
            self._dummy_submission(client)
            resp = client.post('/submit', data=dict(
                msg="AA" * (1024 * 512),
                fh=(StringIO(''), ''),
            ), follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Thanks! We received your message", resp.data)

    def test_submit_file(self):
        with self.client as client:
            new_codename(client, session)
            self._dummy_submission(client)
            resp = client.post('/submit', data=dict(
                msg="",
                fh=(StringIO('This is a test'), 'test.txt'),
            ), follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Thanks! We received your document', resp.data)

    def test_submit_both(self):
        with self.client as client:
            new_codename(client, session)
            self._dummy_submission(client)
            resp = client.post('/submit', data=dict(
                msg="This is a test",
                fh=(StringIO('This is a test'), 'test.txt'),
            ), follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Thanks! We received your message and document",
                          resp.data)

    def test_delete_all_successfully_deletes_replies(self):
        journalist, _ = utils.db_helper.init_journalist()
        source, codename = utils.db_helper.init_source()
        utils.db_helper.reply(journalist, source, 1)
        with self.client as c:
            resp = c.post('/login', data=dict(codename=codename),
                          follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            resp = c.post('/delete-all', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("All replies have been deleted", resp.data)

    @patch('source.app.logger.error')
    def test_delete_all_replies_already_deleted(self, logger):
        journalist, _ = utils.db_helper.init_journalist()
        source, codename = utils.db_helper.init_source()
        # Note that we are creating the source and no replies

        with self.client as c:
            resp = c.post('/login', data=dict(codename=codename),
                          follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            resp = c.post('/delete-all', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            logger.assert_called_once_with(
                "Found no replies when at least one was expected"
            )

    @patch('gzip.GzipFile', wraps=gzip.GzipFile)
    def test_submit_sanitizes_filename(self, gzipfile):
        """Test that upload file name is sanitized"""
        insecure_filename = '../../bin/gpg'
        sanitized_filename = 'bin_gpg'

        with self.client as client:
            new_codename(client, session)
            client.post('/submit', data=dict(
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
        self.assertEqual(json.loads(resp.data.decode('utf-8')).get(
            'sd_version'), version.__version__)

    @patch('crypto_util.hash_codename')
    def test_login_with_overly_long_codename(self, mock_hash_codename):
        """Attempting to login with an overly long codename should result in
        an error, and scrypt should not be called to avoid DoS."""
        with self.client as c:
            resp = c.post('/login', data=dict(codename=overly_long_codename),
                          follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Field must be between 1 and {} "
                          "characters long.".format(Source.MAX_CODENAME_LEN),
                          resp.data)
            self.assertFalse(mock_hash_codename.called,
                             "Called hash_codename for codename w/ invalid "
                             "length")

    @patch('source.app.logger.warning')
    @patch('subprocess.call', return_value=1)
    def test_failed_normalize_timestamps_logs_warning(self, call, logger):
        """If a normalize timestamps event fails, the subprocess that calls
        touch will fail and exit 1. When this happens, the submission should
        still occur, but a warning should be logged (this will trigger an
        OSSEC alert)."""

        with self.client as client:
            new_codename(client, session)
            self._dummy_submission(client)
            resp = client.post('/submit', data=dict(
                msg="This is a test.",
                fh=(StringIO(''), ''),
            ), follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Thanks! We received your message", resp.data)

            logger.assert_called_once_with(
                "Couldn't normalize submission "
                "timestamps (touch exited with 1)"
            )

    @patch('source.app.logger.error')
    def test_source_is_deleted_while_logged_in(self, logger):
        """If a source is deleted by a journalist when they are logged in,
        a NoResultFound will occur. The source should be redirected to the
        index when this happens, and a warning logged."""

        with self.client as client:
            codename = new_codename(client, session)
            resp = client.post('login', data=dict(codename=codename),
                               follow_redirects=True)

            # Now the journalist deletes the source
            filesystem_id = crypto_util.hash_codename(codename)
            crypto_util.delete_reply_keypair(filesystem_id)
            source = Source.query.filter_by(filesystem_id=filesystem_id).one()
            db_session.delete(source)
            db_session.commit()

            # Source attempts to continue to navigate
            resp = client.post('/lookup', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Submit documents for the first time', resp.data)
            self.assertNotIn('logged_in', session.keys())
            self.assertNotIn('codename', session.keys())

        logger.assert_called_once_with(
            "Found no Sources when one was expected: "
            "No row was found for one()")

    def test_login_with_invalid_codename(self):
        """Logging in with a codename with invalid characters should return
        an informative message to the user."""

        invalid_codename = '[]'

        with self.client as c:
            resp = c.post('/login', data=dict(codename=invalid_codename),
                          follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid input.", resp.data)

    def _test_source_session_expiration(self):
        try:
            old_expiration = config.SESSION_EXPIRATION_MINUTES
            has_session_expiration = True
        except AttributeError:
            has_session_expiration = False

        try:
            with self.client as client:
                codename = new_codename(client, session)

                # set the expiration to ensure we trigger an expiration
                config.SESSION_EXPIRATION_MINUTES = -1

                resp = client.post('/login',
                                   data=dict(codename=codename),
                                   follow_redirects=True)
                assert resp.status_code == 200
                resp = client.get('/lookup', follow_redirects=True)

                # check that the session was cleared (apart from 'expires'
                # which is always present and 'csrf_token' which leaks no info)
                session.pop('expires', None)
                session.pop('csrf_token', None)
                assert not session, session
                assert ('You have been logged out due to inactivity' in
                        resp.data.decode('utf-8'))
        finally:
            if has_session_expiration:
                config.SESSION_EXPIRATION_MINUTES = old_expiration
            else:
                del config.SESSION_EXPIRATION_MINUTES

    def test_csrf_error_page(self):
        old_enabled = self.app.config['WTF_CSRF_ENABLED']
        self.app.config['WTF_CSRF_ENABLED'] = True

        try:
            with self.app.test_client() as app:
                resp = app.post(url_for('main.create'))
                self.assertRedirects(resp, url_for('main.index'))

                resp = app.post(url_for('main.create'), follow_redirects=True)
                self.assertIn('Your session timed out due to inactivity',
                              resp.data)
        finally:
            self.app.config['WTF_CSRF_ENABLED'] = old_enabled
