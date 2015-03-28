#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from cStringIO import StringIO
import unittest
import zipfile

import mock

from flask import url_for
from flask.ext.testing import TestCase

import crypto_util
import journalist
import common
from db import db_session, Source, Journalist

# Set environment variable so config.py uses a test environment
os.environ['SECUREDROP_ENV'] = 'test'


class TestJournalist(TestCase):

    def create_app(self):
        return journalist.app

    def setUp(self):
        common.shared_setup()

        # Patch the two-factor verification to avoid intermittent errors
        patcher = mock.patch('db.Journalist.verify_token')
        self.addCleanup(patcher.stop)
        self.mock_journalist_verify_token = patcher.start()
        self.mock_journalist_verify_token.return_value = True

        # Set up test users
        self.user_pw = "bar"
        self.user = Journalist(username="foo",
                               password=self.user_pw)
        self.admin_user_pw = "admin"
        self.admin_user = Journalist(username="admin",
                                     password=self.admin_user_pw,
                                     is_admin=True)
        db_session.add(self.user)
        db_session.add(self.admin_user)
        db_session.commit()

    def tearDown(self):
        common.shared_teardown()

    def test_index_should_redirect_to_login(self):
        res = self.client.get(url_for('index'))
        self.assert_redirects(res, url_for('login'))

    def test_invalid_user_login_should_fail(self):
        res = self.client.post(url_for('login'), data=dict(
            username='invalid',
            password='invalid',
            token='123456'))
        self.assert200(res)
        self.assertIn("Login failed", res.data)

    def test_valid_user_login_should_succeed(self):
        res = self.client.post(url_for('login'), data=dict(
            username=self.user.username,
            password=self.user_pw,
            token=self.user.totp.now()),
            follow_redirects=True)

        self.assert200(res)  # successful login redirects to index
        self.assertIn("Sources", res.data)
        self.assertIn("No documents have been submitted!", res.data)

    def test_normal_and_admin_user_login_should_redirect_to_index(self):
        """Normal users and admin users should both redirect
           to the index page after logging in successfully"""
        res = self.client.post(url_for('login'), data=dict(
            username=self.user.username,
            password=self.user_pw,
            token=self.user.totp.now()))
        self.assert_redirects(res, url_for('index'))

        res = self.client.post(url_for('login'), data=dict(
            username=self.admin_user.username,
            password=self.admin_user_pw,
            token=self.admin_user.totp.now()))
        self.assert_redirects(res, url_for('index'))

    def test_admin_user_has_admin_link_in_index(self):
        res = self.client.post(url_for('login'), data=dict(
            username=self.admin_user.username,
            password=self.admin_user_pw,
            token=self.admin_user.totp.now()),
            follow_redirects=True)
        admin_link = '<a href="{}">{}</a>'.format(
            url_for('admin_index'),
            "Admin")
        self.assertIn(admin_link, res.data)

    def _login_user(self):
        self.client.post(url_for('login'), data=dict(
            username=self.user.username,
            password=self.user_pw,
            token=self.user.totp.now()),
            follow_redirects=True)

    def _login_admin(self):
        self.client.post(url_for('login'), data=dict(
            username=self.admin_user.username,
            password=self.admin_user_pw,
            token=self.admin_user.totp.now()),
            follow_redirects=True)

    def test_admin_index(self):
        self._login_admin()
        res = self.client.get(url_for('admin_index'))
        self.assert200(res)
        self.assertIn("Admin Interface", res.data)

    # TODO: more tests for admin interface

    def test_bulk_download(self):
        sid = ('EQZGCJBRGISGOTC2NZVWG6LILJBHEV3CINNEWSCLLFTUWZJPKJFECLS2N'
               'Z4G4U3QOZCFKTTPNZMVIWDCJBBHMUDBGFHXCQ3R')
        source = Source(sid, crypto_util.display_id())
        db_session.add(source)
        db_session.commit()
        files = ['1-abc1-msg.gpg', '2-abc2-msg.gpg']
        filenames = common.setup_test_docs(sid, files)

        self._login_user()
        rv = self.client.post('/bulk', data=dict(
            action='download',
            sid=sid,
            doc_names_selected=files
        ))

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.content_type, 'application/zip')
        self.assertTrue(zipfile.is_zipfile(StringIO(rv.data)))
        self.assertTrue(zipfile.ZipFile(StringIO(rv.data)).getinfo(
            os.path.join(source.journalist_filename, files[0])
        ))


if __name__ == "__main__":
    unittest.main(verbosity=2)
