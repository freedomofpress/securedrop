#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fnmatch
import mock
import os
from StringIO import StringIO
import unittest

import manage

ABS_MODULE_PATH = os.path.dirname(os.path.abspath(__file__))

class TestManagePy(unittest.TestCase):

    def setUp(self):
        self.parser = manage.get_args()

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_invalid_unit_test_names_fail(self, mock_stdout):
        args = self.parser.parse_args('unit -t crypto_util db.py'.split())
        rc = manage._get_pytest_cmd_from_args(args, 'unit')
        self.assertEqual(rc, 1)
        self.assertTrue(
            mock_stdout.getvalue().startswith('No unit test "db.py" found.'))

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_invalid_functional(self, mock_stdout):
        args = self.parser.parse_args(
            'functional -t admin_interface.py'.split())
        rc = manage._get_pytest_cmd_from_args(args, 'functional')
        self.assertEqual(rc, 1)
        self.assertTrue(
            mock_stdout.getvalue().startswith('No functional test '
                                              '"admin_interface.py" found.'))

    def test_pytest_parse_args_single_unit(self):
        args = self.parser.parse_args('unit -t crypto_util'.split())
        cmd = manage._get_pytest_cmd_from_args(args, 'unit')
        self.assertRegexpMatches(
            cmd, 'pytest -- /[a-z/]+/tests/test_unit_crypto_util.py')
    
    def test_pytest_cmd(self):
        args = self.parser.parse_args(
            'pytest -- tests/test_unit_db.py::TestDatabase::'
            'test_get_one_or_else_multiple_results --pdb'.split())
        cmd = manage._get_pytest_cmd_from_args(args, 'unit')
        self.assertEqual(cmd, 'pytest tests/test_unit_db.py::TestDatabase::'
                         'test_get_one_or_else_multiple_results --pdb ')

    def test_pytest_parse_args_all_units(self):
        args = self.parser.parse_args('unit -a'.split())
        cmd = manage._get_pytest_cmd_from_args(args, 'unit')
        self.assertRegexpMatches(cmd, 'pytest --cov -- [a-z/_]+.py')
        self.assertRegexpMatches(cmd, '/tests/test_unit')

    def test_pytest_parse_args_single_functional(self):
        args = self.parser.parse_args('functional -t admin_interface'.split())
        cmd = manage._get_pytest_cmd_from_args(args, 'functional')
        self.assertRegexpMatches(
            cmd, 'pytest -- /[a-z/]+/tests/functional/test_admin_interface.py')

    def test_pytest_parse_args_all_functionals(self):
        args = self.parser.parse_args('functional -a'.split())
        cmd = manage._get_pytest_cmd_from_args(args, 'functional')
        self.assertRegexpMatches(cmd, 'pytest --cov -- [a-z/_]+.py')
        self.assertRegexpMatches(cmd, '/tests/functional/test_')

    def test_pytest_parse_args_all_tests(self):
        args = self.parser.parse_args('functional -a'.split())
        cmd = manage._get_pytest_cmd_from_args(args, 'functional')
        self.assertRegexpMatches(cmd, 'pytest --cov -- [a-z/_]+.py')

    def test_get_test_module_dict_functional(self):
        output = manage._get_test_module_dict('functional')
        # All test modules should be present
        for file in os.listdir(os.path.join(ABS_MODULE_PATH, "functional")):
            if fnmatch.fnmatch(file, 'test*.py'):
                self.assertIn(os.path.join(ABS_MODULE_PATH, 'functional',
                                           file),
                              output.values())
        # The test modules short names should not contain path, extension, or
        # other unecessary text
        for test in list(output):
            self.assertNotRegexpMatches(ABS_MODULE_PATH, test)
            self.assertNotRegexpMatches('test_', test)
            self.assertNotRegexpMatches('py', test)
        # The short name (key) should be a substring of the test's path
        for test, test_path in output.items():
            self.assertRegexpMatches(test_path, test)

    def test_get_test_module_dict_unit(self):
        output = manage._get_test_module_dict('unit')
        # All test modules should be present
        for file in os.listdir(ABS_MODULE_PATH):
            if fnmatch.fnmatch(file, 'test*.py'):
                self.assertIn(os.path.join(ABS_MODULE_PATH, file),
                              output.values())
        # The test modules short names should not contain path, extension, or
        # other unecessary text
        for test in list(output):
            self.assertNotRegexpMatches(ABS_MODULE_PATH, test)
            # For app code modules for which there are multiple corresponding
            # unit test modules, one will be prefixed by 'test'.
            self.assertNotRegexpMatches('test_unit', test)
            self.assertNotRegexpMatches('py', test)
        # The short name (key) should be a substring of the test's path
        for test, test_path in output.items():
            self.assertRegexpMatches(test_path, test)
