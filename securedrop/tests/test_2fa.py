# -*- coding: utf-8 -*-
import os

from flask import url_for
import flask_testing

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
from db import Journalist, BadTokenException
import journalist
import utils


class TestJournalist2FA(flask_testing.TestCase):
    def create_app(self):
        return journalist.app

    def setUp(self):
        utils.env.setup()
        self.admin, self.admin_pw = utils.db_helper.init_journalist(
            is_admin=True)
        self.user, self.user_pw = utils.db_helper.init_journalist()

    def tearDown(self):
        utils.env.teardown()

    def _login_admin(self, token=None):
        """Login to the Journalist Interface as an admin user with the
        Werkzeug client.

        Args:
            token (str): The TOTP token to attempt login with. Defaults
                to the correct token for the current time window.
        """
        if token is None:
            token = self.admin.totp.now()
        self.client.post(url_for('main.login'),
                         data=dict(username=self.admin.username,
                                   password=self.admin_pw,
                                   token=token))

    def _login_user(self, token=None):
        """Analagous to `_login_admin()` except for a non-admin user.
        """
        if token is None:
            token = self.user.totp.now()
        resp = self.client.post(url_for('main.login'),
                                data=dict(username=self.user.username,
                                          password=self.user_pw,
                                          token=token))
        return resp

    def test_totp_reuse_protections(self):
        """Ensure that logging in twice with the same TOTP token
        fails.
        """
        token = self.user.totp.now()
        resp = self._login_user(token)
        self.assertRedirects(resp, url_for('main.index'))

        resp = self._login_user(token)
        self.assert200(resp)
        self.assertIn("Login failed", resp.data)

    def test_totp_reuse_protections2(self):
        """More granular than the preceeding test, we want to make sure
        the right exception is being raised in the right place.
        """
        valid_token = self.user.totp.now()
        Journalist.login(self.user.username, self.user_pw, valid_token)
        with self.assertRaises(BadTokenException):
            Journalist.login(self.user.username, self.user_pw, valid_token)

    def test_bad_token_fails_to_verify_on_admin_new_user_two_factor_page(self):
        # Regression test
        # https://github.com/freedomofpress/securedrop/pull/1692
        self._login_admin()

        # Create and submit an invalid 2FA token
        invalid_token = u'000000'
        resp = self.client.post(url_for('admin.new_user_two_factor',
                                        uid=self.admin.id),
                                data=dict(token=invalid_token))

        self.assert200(resp)
        self.assertMessageFlashed(
            'Could not verify token in two-factor authentication.', 'error')
        # last_token should be set to the invalid token we just tried to use
        self.assertEqual(self.admin.last_token, invalid_token)

        # Submit the same invalid token again
        resp = self.client.post(url_for('admin.new_user_two_factor',
                                        uid=self.admin.id),
                                data=dict(token=invalid_token))

        # A flashed message should appear
        self.assertMessageFlashed(
            'Could not verify token in two-factor authentication.', 'error')

    def test_bad_token_fails_to_verify_on_new_user_two_factor_page(self):
        # Regression test
        # https://github.com/freedomofpress/securedrop/pull/1692
        self._login_user()

        # Create and submit an invalid 2FA token
        invalid_token = u'000000'
        resp = self.client.post(url_for('account.new_two_factor'),
                                data=dict(token=invalid_token))

        self.assert200(resp)
        self.assertMessageFlashed(
            'Could not verify token in two-factor authentication.', 'error')
        # last_token should be set to the invalid token we just tried to use
        self.assertEqual(self.user.last_token, invalid_token)

        # Submit the same invalid token again
        resp = self.client.post(url_for('account.new_two_factor'),
                                data=dict(token=invalid_token))

        # A flashed message should appear
        self.assertMessageFlashed(
            'Could not verify token in two-factor authentication.', 'error')
