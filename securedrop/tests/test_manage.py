# -*- coding: utf-8 -*-

import argparse
import os
os.environ['SECUREDROP_ENV'] = 'test'  # noqa
import config
import logging
import manage
import mock
import pytest
from StringIO import StringIO
import subprocess
import sys
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

    def test_translate_compile_code_and_template(self):
        source = [
            'tests/i18n/code.py',
            'tests/i18n/template.html',
        ]
        kwargs = {
            'translations_dir': config.TEMP_DIR,
            'mapping': 'tests/i18n/babel.cfg',
            'source': source,
            'extract_update': True,
            'compile': True,
            'verbose': logging.DEBUG,
        }
        args = argparse.Namespace(**kwargs)
        manage.setup_verbosity(args)
        manage.translate(args)
        messages_file = os.path.join(config.TEMP_DIR, 'messages.pot')
        assert os.path.exists(messages_file)
        pot = open(messages_file).read()
        assert 'code hello i18n' in pot
        assert 'template hello i18n' in pot

        locale = 'en_US'
        locale_dir = os.path.join(config.TEMP_DIR, locale)
        manage.sh("pybabel init -i {} -d {} -l {}".format(
            messages_file,
            config.TEMP_DIR,
            locale,
        ))
        mo_file = os.path.join(locale_dir, 'LC_MESSAGES/messages.mo')
        assert not os.path.exists(mo_file)
        manage.translate(args)
        assert os.path.exists(mo_file)
        mo = open(mo_file).read()
        assert 'code hello i18n' in mo
        assert 'template hello i18n' in mo

    def test_translate_compile_arg(self):
        source = [
            'tests/i18n/code.py',
        ]
        kwargs = {
            'translations_dir': config.TEMP_DIR,
            'mapping': 'tests/i18n/babel.cfg',
            'source': source,
            'extract_update': True,
            'compile': False,
            'verbose': logging.DEBUG,
        }
        args = argparse.Namespace(**kwargs)
        manage.setup_verbosity(args)
        manage.translate(args)
        messages_file = os.path.join(config.TEMP_DIR, 'messages.pot')
        assert os.path.exists(messages_file)
        pot = open(messages_file).read()
        assert 'code hello i18n' in pot

        locale = 'en_US'
        locale_dir = os.path.join(config.TEMP_DIR, locale)
        manage.sh("pybabel init -i {} -d {} -l {}".format(
            messages_file,
            config.TEMP_DIR,
            locale,
        ))
        mo_file = os.path.join(locale_dir, 'LC_MESSAGES/messages.mo')

        #
        # Extract+update but do not compile
        #
        assert not os.path.exists(mo_file)
        manage.translate(args)
        assert not os.path.exists(mo_file)

        #
        # Compile but do not extract+update
        #
        source = [
            'tests/i18n/code.py',
            'tests/i18n/template.html',
        ]
        kwargs['extract_update'] = False
        kwargs['compile'] = True
        args = argparse.Namespace(**kwargs)
        manage.translate(args)
        mo = open(mo_file).read()
        assert 'code hello i18n' in mo
        assert 'template hello i18n' not in mo


class TestSh(object):

    def test_sh(self):
        assert 'A' == manage.sh("echo -n A")
        with pytest.raises(Exception) as excinfo:
            manage.sh("exit 123")
        assert excinfo.value.returncode == 123

    def test_sh_progress(self, caplog):
        manage.sh("echo AB ; sleep 5 ; echo C")
        records = caplog.records()
        assert ':sh: ' in records[0].message
        assert 'AB' == records[1].message
        assert 'C' == records[2].message

    def test_sh_input(self, caplog):
        assert 'abc' == manage.sh("cat", 'abc')

    def test_sh_fail(self, caplog):
        with pytest.raises(subprocess.CalledProcessError) as excinfo:
            manage.sh("/bin/echo -n AB ; /bin/echo C ; exit 111")
        assert excinfo.value.returncode == 111
        for record in caplog.records():
            if record.levelname == 'ERROR':
                assert ('replay full' in record.message or
                        'ABC\n' == record.message)
