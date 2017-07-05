# -*- coding: utf-8 -*-

import manage
import mock
from StringIO import StringIO
import sys
import unittest

import utils


class TestManagePy(unittest.TestCase):
    def test_parse_args(self):
        # just test that the arg parser is stable
        manage.get_args()


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
