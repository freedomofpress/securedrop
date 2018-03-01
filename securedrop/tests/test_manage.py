# -*- coding: utf-8 -*-

import argparse
import os
from os.path import abspath, dirname, realpath
os.environ['SECUREDROP_ENV'] = 'test'  # noqa
from sdconfig import config
import logging
import manage
import mock
from sqlalchemy.orm.exc import NoResultFound
from StringIO import StringIO
import sys
import time
import unittest
import utils

import journalist_app

from db import db
from models import Journalist


YUBIKEY_HOTP = ['cb a0 5f ad 41 a2 ff 4e eb 53 56 3a 1b f7 23 2e ce fc dc',
                'cb a0 5f ad 41 a2 ff 4e eb 53 56 3a 1b f7 23 2e ce fc dc d7']


class TestManagePy(object):

    def test_parse_args(self):
        # just test that the arg parser is stable
        manage.get_args()

    def test_not_verbose(self, caplog):
        args = manage.get_args().parse_args(['run'])
        manage.setup_verbosity(args)
        manage.log.debug('INVISIBLE')
        assert 'INVISIBLE' not in caplog.text

    def test_verbose(self, caplog):
        args = manage.get_args().parse_args(['--verbose', 'run'])
        manage.setup_verbosity(args)
        manage.log.debug('VISIBLE')
        assert 'VISIBLE' in caplog.text


class TestManagementCommand(unittest.TestCase):

    def setUp(self):
        self.__context = journalist_app.create_app(config).app_context()
        self.__context.push()
        utils.env.setup()
        self.__context.pop()

    def tearDown(self):
        self.__context.push()
        utils.env.teardown()
        self.__context.pop()

    @mock.patch("__builtin__.raw_input", return_value='jen')
    def test_get_username_success(self, mock_stdin):
        assert manage._get_username() == 'jen'

    @mock.patch("__builtin__.raw_input",
                side_effect=['a' * (Journalist.MIN_USERNAME_LEN - 1), 'jen'])
    def test_get_username_fail(self, mock_stdin):
        assert manage._get_username() == 'jen'

    @mock.patch("__builtin__.raw_input", return_value='y')
    def test_get_yubikey_usage_yes(self, mock_stdin):
        assert manage._get_yubikey_usage()

    @mock.patch("__builtin__.raw_input", return_value='n')
    def test_get_yubikey_usage_no(self, mock_stdin):
        assert not manage._get_yubikey_usage()

    @mock.patch("manage._get_username", return_value='ntoll')
    @mock.patch("manage._get_yubikey_usage", return_value=True)
    @mock.patch("__builtin__.raw_input", side_effect=YUBIKEY_HOTP)
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_handle_invalid_secret(self, mock_username, mock_yubikey,
                                   mock_htop, mock_stdout):
        """Regression test for bad secret logic in manage.py"""

        # We will try to provide one invalid and one valid secret
        return_value = manage._add_user()
        self.assertEqual(return_value, 0)
        self.assertIn('Try again.', sys.stdout.getvalue())
        self.assertIn('successfully added', sys.stdout.getvalue())

    @mock.patch("manage._get_username", return_value='foo-bar-baz')
    @mock.patch("manage._get_yubikey_usage", return_value=False)
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_exception_handling_when_duplicate_username(self,
                                                        mock_username,
                                                        mock_yubikey,
                                                        mock_stdout):
        """Regression test for duplicate username logic in manage.py"""

        # Inserting the user for the first time should succeed
        return_value = manage._add_user()
        self.assertEqual(return_value, 0)
        self.assertIn('successfully added', sys.stdout.getvalue())

        # Inserting the user for a second time should fail
        return_value = manage._add_user()
        self.assertEqual(return_value, 1)
        self.assertIn('ERROR: That username is already taken!',
                      sys.stdout.getvalue())

    @mock.patch("manage._get_username", return_value='test-user-56789')
    @mock.patch("manage._get_yubikey_usage", return_value=False)
    @mock.patch("manage._get_username_to_delete",
                return_value='test-user-56789')
    @mock.patch('manage._get_delete_confirmation', return_value=True)
    def test_delete_user(self,
                         mock_username,
                         mock_yubikey,
                         mock_user_to_delete,
                         mock_user_del_confirm):
        return_value = manage._add_user()
        self.assertEqual(return_value, 0)

        return_value = manage.delete_user(args=None)
        self.assertEqual(return_value, 0)

    @mock.patch("manage._get_username_to_delete",
                return_value='does-not-exist')
    @mock.patch('manage._get_delete_confirmation', return_value=True)
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_delete_non_existent_user(self,
                                      mock_user_to_delete,
                                      mock_user_del_confirm,
                                      mock_stdout):
        return_value = manage.delete_user(args=None)
        self.assertEqual(return_value, 0)
        self.assertIn('ERROR: That user was not found!',
                      sys.stdout.getvalue())

    @mock.patch("__builtin__.raw_input", return_value='test-user-12345')
    def test_get_username_to_delete(self, mock_username):
        return_value = manage._get_username_to_delete()
        self.assertEqual(return_value, 'test-user-12345')

    def test_reset(self):
        test_journalist, _ = utils.db_helper.init_journalist()
        user_should_be_gone = test_journalist.username

        return_value = manage.reset(args=None)

        self.assertEqual(return_value, 0)
        assert os.path.exists(config.DATABASE_FILE)
        assert os.path.exists(config.STORE_DIR)

        # Verify journalist user present in the database is gone
        db.session.remove()  # Close session and get a session on the new db
        with self.assertRaises(NoResultFound):
            Journalist.query.filter_by(username=user_should_be_gone).one()


class TestManage(object):

    def setup(self):
        self.__context = journalist_app.create_app(config).app_context()
        self.__context.push()
        self.dir = abspath(dirname(realpath(__file__)))
        utils.env.setup()

    def teardown(self):
        utils.env.teardown()
        self.__context.pop()

    @mock.patch("__builtin__.raw_input", return_value='foo-bar-baz')
    def test_get_username(self, mock_get_usernam):
        assert manage._get_username() == 'foo-bar-baz'

    def test_clean_tmp_do_nothing(self, caplog):
        args = argparse.Namespace(days=0,
                                  directory=' UNLIKELY ',
                                  verbose=logging.DEBUG)
        manage.setup_verbosity(args)
        manage.clean_tmp(args)
        assert 'does not exist, do nothing' in caplog.text

    def test_clean_tmp_too_young(self, caplog):
        args = argparse.Namespace(days=24*60*60,
                                  directory=config.TEMP_DIR,
                                  verbose=logging.DEBUG)
        open(os.path.join(config.TEMP_DIR, 'FILE'), 'a').close()
        manage.setup_verbosity(args)
        manage.clean_tmp(args)
        assert 'modified less than' in caplog.text

    def test_clean_tmp_removed(self, caplog):
        args = argparse.Namespace(days=0,
                                  directory=config.TEMP_DIR,
                                  verbose=logging.DEBUG)
        fname = os.path.join(config.TEMP_DIR, 'FILE')
        with open(fname, 'a'):
            old = time.time() - 24*60*60
            os.utime(fname, (old, old))
        manage.setup_verbosity(args)
        manage.clean_tmp(args)
        assert 'FILE removed' in caplog.text
