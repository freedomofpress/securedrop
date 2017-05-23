# -*- coding: utf-8 -*-
import os
import random

from flask import url_for
from flask_testing import TestCase

os.environ['SECUREDROP_ENV'] = 'test'
from db import db_session
import journalist
import utils

# Smugly seed the RNG for deterministic testing
random.seed('¯\_(ツ)_/¯')


class TestJournalist2FA(TestCase):
    def create_app(self):
        return journalist.app

    def setUp(self):
        utils.env.setup()

        self.admin, self.admin_pw = utils.db_helper.init_journalist(
            is_admin=True)
        self.user, self.user_pw = utils.db_helper.init_journalist()

    def tearDown(self):
        utils.env.teardown()

    def _login_admin(self):
        valid_token = self.admin.totp.now()
        resp = self.client.post(url_for('login'),
                                data=dict(username=self.admin.username,
                                          password=self.admin_pw,
                                          token=valid_token))

    def _login_user(self):
        valid_token = self.user.totp.now()
        resp = self.client.post(url_for('login'),
                                data=dict(username=self.user.username,
                                          password=self.user_pw,
                                          token=valid_token))

    def test_bad_token_fails_to_verify_on_admin_new_user_two_factor_page(self):
        # Regression test https://github.com/freedomofpress/securedrop/pull/1692
        self._login_admin()

        # Create and submit an invalid 2FA token
        invalid_token = u'000000'
        resp = self.client.post(url_for('admin_new_user_two_factor',
                                        uid=self.admin.id),
                                data=dict(token=invalid_token))

        self.assertIn('Two factor token failed to verify', resp.data)

        # last_token should be set to the invalid token we just tried to use
        self.assertEqual(self.admin.last_token, invalid_token)

        # Submit the same invalid token again
        resp = self.client.post(url_for('admin_new_user_two_factor',
                                        uid=self.admin.id),
                                data=dict(token=invalid_token))

        # A flashed message should appear
        self.assertIn('Two factor token failed to verify', resp.data)

    def test_bad_token_fails_to_verify_on_new_user_two_factor_page(self):
        # Regression test https://github.com/freedomofpress/securedrop/pull/1692
        self._login_user()

        # Create and submit an invalid 2FA token
        invalid_token = u'000000'
        resp = self.client.post(url_for('account_new_two_factor'),
                                data=dict(token=invalid_token))

        self.assertIn('Two factor token failed to verify', resp.data)

        # last_token should be set to the invalid token we just tried to use
        self.assertEqual(self.user.last_token, invalid_token)

        # Submit the same invalid token again
        resp = self.client.post(url_for('account_new_two_factor'),
                                data=dict(token=invalid_token))

        # A flashed message should appear
        self.assertIn('Two factor token failed to verify', resp.data)

    @classmethod
    def tearDownClass(cls):
        # Reset the module variables that were changed to mocks so we don't
        # break other tests
        reload(journalist)
