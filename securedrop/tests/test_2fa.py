# -*- coding: utf-8 -*-
import os
import pytest
import time

from contextlib import contextmanager
from datetime import datetime, timedelta
from flask import url_for
from pyotp import TOTP
import flask_testing

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
from models import Journalist, BadTokenException
from utils.instrument import InstrumentedApp

import models
import journalist
import utils


@contextmanager
def totp_window():
    # To ensure we have enough time during a single TOTP window to do the
    # whole test, optionally sleep.
    now = datetime.now()
    mod = now.second % 30
    if mod < 3:
        time.sleep(mod % 30)
        now = datetime.now()

    yield

    # This check ensures that the token was used during the same window
    # in the event that the app's logic only checks for token reuse if the
    # token was valid.
    then = datetime.now()
    assert then < now + timedelta(seconds=(30 - mod))


def test_totp_reuse_protections(journalist_app, test_journo):
    """Ensure that logging in twice with the same TOTP token fails."""
    original_hardening = models.LOGIN_HARDENING
    try:
        models.LOGIN_HARDENING = True

        with totp_window():
            token = TOTP(test_journo['otp_secret']).now()

            with journalist_app.test_client() as app:
                with InstrumentedApp(journalist_app) as ins:
                    resp = app.post('/login',
                                    data=dict(username=test_journo['username'],
                                              password=test_journo['password'],
                                              token=token))
                    ins.assert_redirects(resp, '/')
                resp = app.get('/logout', follow_redirects=True)
                assert resp.status_code == 200

            with journalist_app.test_client() as app:
                resp = app.post('/login',
                                data=dict(username=test_journo['username'],
                                          password=test_journo['password'],
                                          token=token))
                assert resp.status_code == 200
                text = resp.data.decode('utf-8')
                assert "Login failed" in text
    finally:
        models.LOGIN_HARDENING = original_hardening


def test_totp_reuse_protections2(journalist_app, test_journo):
    """More granular than the preceeding test, we want to make sure the right
       exception is being raised in the right place.
    """
    original_hardening = models.LOGIN_HARDENING
    try:
        models.LOGIN_HARDENING = True

        with totp_window():
            token = TOTP(test_journo['otp_secret']).now()

            with journalist_app.app_context():
                Journalist.login(test_journo['username'],
                                 test_journo['password'],
                                 token)
                with pytest.raises(BadTokenException):
                    Journalist.login(test_journo['username'],
                                     test_journo['password'],
                                     token)
    finally:
        models.LOGIN_HARDENING = original_hardening


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
