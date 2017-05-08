# -*- coding: utf-8 -*-
import os
import random

from flask import url_for
from flask_testing import TestCase

os.environ['SECUREDROP_ENV'] = 'test'
from db import (db_session, BadTokenException)
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

    def tearDown(self):
        utils.env.teardown()
        # TODO: figure out why this is necessary here, but unnecessary in all
        # of the tests in `tests/test_unit_*.py`. Without this, the session
        # continues to return values even if the underlying database is deleted
        # (as in `shared_teardown`).
        db_session.remove()

    def _login_admin(self):
        valid_token = self.admin.totp.now()
        resp = self.client.post(url_for('login'),
                                data=dict(username=self.admin.username,
                                          password=self.admin_pw,
                                          token=valid_token))

    def test_bad_token_fails_to_verify_on_admin_new_user_two_factor_page(self):
        self._login_admin()

        # Create and submit an invalid 2FA token
        invalid_token = unicode(int(self.admin.totp.now()) + 1)
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

    @classmethod
    def tearDownClass(cls):
        # Reset the module variables that were changed to mocks so we don't
        # break other tests
        reload(journalist)
