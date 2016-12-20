#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from mock import patch, ANY, MagicMock
import unittest

from db import db_session, InvalidPasswordLength, Journalist
import journalist
import utils

class TestJournalistApp(unittest.TestCase):

    def setUp(self):
        journalist.logged_in = MagicMock()
        journalist.request = MagicMock()
        journalist.url_for = MagicMock()
        journalist.redirect = MagicMock()
        journalist.abort = MagicMock()
        journalist.db_session = MagicMock()
        journalist.get_docs = MagicMock()
        journalist.get_or_else = MagicMock()

    def _set_up_request(self, cols_selected, action):
        journalist.request.form.__contains__.return_value = True
        journalist.request.form.getlist = MagicMock(return_value=cols_selected)
        journalist.request.form.__getitem__.return_value = action

    @patch("journalist.col_delete")
    def test_col_process_delegates_to_col_delete(self, col_delete):
        cols_selected = ['source_id']
        self._set_up_request(cols_selected, 'delete')

        journalist.col_process()

        col_delete.assert_called_with(cols_selected)

    @patch("journalist.col_star")
    def test_col_process_delegates_to_col_star(self, col_star):
        cols_selected = ['source_id']
        self._set_up_request(cols_selected, 'star')

        journalist.col_process()

        col_star.assert_called_with(cols_selected)

    @patch("journalist.col_un_star")
    def test_col_process_delegates_to_col_un_star(self, col_un_star):
        cols_selected = ['source_id']
        self._set_up_request(cols_selected, 'un-star')

        journalist.col_process()

        col_un_star.assert_called_with(cols_selected)

    @patch("journalist.abort")
    def test_col_process_returns_404_with_bad_action(self, abort):
        cols_selected = ['source_id']
        self._set_up_request(cols_selected, 'something-random')

        journalist.col_process()

        abort.assert_called_with(ANY)

    @patch("journalist.make_star_true")
    @patch("journalist.db_session")
    def test_col_star_call_db_(self, db_session, make_star_true):
        journalist.col_star(['sid'])

        make_star_true.assert_called_with('sid')

    @patch("journalist.db_session")
    def test_col_un_star_call_db(self, db_session):
        journalist.col_un_star([])

        db_session.commit.assert_called_with()


    @classmethod
    def tearDownClass(cls):
        # Reset the module variables that were changed to mocks so we don't
        # break other tests
        reload(journalist)


class TestJournalistLogin(unittest.TestCase):

    def setUp(self):
        utils.env.setup()

        # Patch the two-factor verification so it always succeeds
        utils.db_helper.mock_verify_token(self)

        self.user, self.user_pw = utils.db_helper.init_journalist()

    def tearDown(self):
        utils.env.teardown()
        # TODO: figure out why this is necessary here, but unnecessary in all
        # of the tests in `tests/test_unit_*.py`. Without this, the session
        # continues to return values even if the underlying database is deleted
        # (as in `shared_teardown`).
        db_session.remove()

    @patch('db.Journalist._scrypt_hash')
    @patch('db.Journalist.valid_password', return_value=True)
    def test_valid_login_calls_scrypt(self, mock_scrypt_hash, mock_valid_password):
        Journalist.login(self.user.username, self.user_pw, 'mocked')
        self.assertTrue(mock_scrypt_hash.called,
                "Failed to call _scrypt_hash for password w/ valid length")

    @patch('db.Journalist._scrypt_hash')
    def test_login_with_invalid_password_doesnt_call_scrypt(self, mock_scrypt_hash):
        invalid_pw = 'a'*(Journalist.MAX_PASSWORD_LEN + 1)
        with self.assertRaises(InvalidPasswordLength):
            Journalist.login(self.user.username, invalid_pw, 'mocked')
        self.assertFalse(mock_scrypt_hash.called,
                "Called _scrypt_hash for password w/ invalid length")

    @classmethod
    def tearDownClass(cls):
        # Reset the module variables that were changed to mocks so we don't
        # break other tests
        reload(journalist)
