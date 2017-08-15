# -*- coding: utf-8 -*-

import os
import argparse
os.environ['SECUREDROP_ENV'] = 'test'  # noqa
import config
import logging
import manage
import mock
from StringIO import StringIO
import sys
import time
import unittest

import utils


class TestManagePy(object):
    def test_parse_args(self):
        # just test that the arg parser is stable
        manage.get_args()

    def test_not_verbose(self, caplog):
        args = manage.get_args().parse_args(['run'])
        manage.setup_verbosity(args)
        manage.log.debug('INVISIBLE')
        assert 'INVISIBLE' not in caplog.text()

    def test_verbose(self, caplog):
        args = manage.get_args().parse_args(['--verbose', 'run'])
        manage.setup_verbosity(args)
        manage.log.debug('VISIBLE')
        assert 'VISIBLE' in caplog.text()


class TestManagementCommand(unittest.TestCase):
    def setUp(self):
        utils.env.setup()

    def tearDown(self):
        utils.env.teardown()

    @mock.patch("__builtin__.raw_input", return_value='N')
    @mock.patch("manage.getpass", return_value='testtesttest')
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_exception_handling_when_duplicate_username(self, mock_raw_input,
                                                        mock_getpass,
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


class TestManage(object):

    def setup(self):
        utils.env.setup()

    def teardown(self):
        utils.env.teardown()

    def test_clean_tmp_do_nothing(self, caplog):
        args = argparse.Namespace(days=0,
                                  directory=' UNLIKELY ',
                                  verbose=logging.DEBUG)
        manage.setup_verbosity(args)
        manage.clean_tmp(args)
        assert 'does not exist, do nothing' in caplog.text()

    def test_clean_tmp_too_young(self, caplog):
        args = argparse.Namespace(days=24*60*60,
                                  directory=config.TEMP_DIR,
                                  verbose=logging.DEBUG)
        open(os.path.join(config.TEMP_DIR, 'FILE'), 'a').close()
        manage.setup_verbosity(args)
        manage.clean_tmp(args)
        assert 'modified less than' in caplog.text()

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
        assert 'FILE removed' in caplog.text()
