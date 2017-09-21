# -*- coding: utf-8 -*-

import argparse
import os
from os.path import abspath, dirname, exists, getmtime, join, realpath
os.environ['SECUREDROP_ENV'] = 'test'  # noqa
import config
import logging
import manage
import mock
import pytest
from StringIO import StringIO
import shutil
import subprocess
import sys
import time
import unittest
import version
import utils

from db import Journalist


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


class TestManage(object):

    def setup(self):
        self.dir = abspath(dirname(realpath(__file__)))
        utils.env.setup()

    def teardown(self):
        utils.env.teardown()

    @mock.patch("__builtin__.raw_input", return_value='foo-bar-baz')
    def test_get_username(self, mock_get_usernam):
        assert manage._get_username() == 'foo-bar-baz'

    def test_translate_desktop_l10n(self):
        in_files = {}
        for what in ('source', 'journalist'):
            in_files[what] = join(config.TEMP_DIR, what + '.desktop.in')
            shutil.copy(join(self.dir, 'i18n/' + what + '.desktop.in'),
                        in_files[what])
        kwargs = {
            'translations_dir': config.TEMP_DIR,
            'source': [in_files['source']],
            'extract_update': True,
            'compile': False,
            'verbose': logging.DEBUG,
            'version': version.__version__,
        }
        args = argparse.Namespace(**kwargs)
        manage.setup_verbosity(args)
        manage.translate_desktop(args)
        messages_file = join(config.TEMP_DIR, 'desktop.pot')
        assert exists(messages_file)
        pot = open(messages_file).read()
        assert 'SecureDrop Source Interfaces' in pot
        # pretend this happened a few seconds ago
        few_seconds_ago = time.time() - 60
        os.utime(messages_file, (few_seconds_ago, few_seconds_ago))

        i18n_file = join(config.TEMP_DIR, 'source.desktop')

        #
        # Extract+update but do not compile
        #
        kwargs['source'] = in_files.values()
        old_messages_mtime = getmtime(messages_file)
        assert not exists(i18n_file)
        manage.translate_desktop(args)
        assert not exists(i18n_file)
        current_messages_mtime = getmtime(messages_file)
        assert old_messages_mtime < current_messages_mtime

        locale = 'fr_FR'
        po_file = join(config.TEMP_DIR, locale + ".po")
        manage.sh("""
        msginit  --no-translator \
                 --locale {locale} \
                 --output {po_file} \
                 --input {messages_file}
        sed -i -e '/{source}/,+1s/msgstr ""/msgstr "SOURCE FR"/' \
                 {po_file}
        """.format(source='SecureDrop Source Interfaces',
                   messages_file=messages_file,
                   po_file=po_file,
                   locale=locale))
        assert exists(po_file)

        #
        # Compile but do not extract+update
        #
        kwargs['source'] = in_files.values() + ['BOOM']
        kwargs['extract_update'] = False
        kwargs['compile'] = True
        args = argparse.Namespace(**kwargs)
        old_messages_mtime = current_messages_mtime
        manage.translate_desktop(args)
        assert old_messages_mtime == getmtime(messages_file)
        po = open(po_file).read()
        assert 'SecureDrop Source Interfaces' in po
        assert 'SecureDrop Journalist Interfaces' not in po
        i18n = open(i18n_file).read()
        assert 'SOURCE FR' in i18n

    def test_translate_messages_l10n(self):
        source = [
            join(self.dir, 'i18n/code.py'),
            join(self.dir, 'i18n/template.html'),
        ]
        kwargs = {
            'translations_dir': config.TEMP_DIR,
            'mapping': join(self.dir, 'i18n/babel.cfg'),
            'source': source,
            'extract_update': True,
            'compile': True,
            'verbose': logging.DEBUG,
            'version': version.__version__,
        }
        args = argparse.Namespace(**kwargs)
        manage.setup_verbosity(args)
        manage.translate_messages(args)
        messages_file = join(config.TEMP_DIR, 'messages.pot')
        assert exists(messages_file)
        pot = open(messages_file).read()
        assert 'code hello i18n' in pot
        assert 'template hello i18n' in pot

        locale = 'en_US'
        locale_dir = join(config.TEMP_DIR, locale)
        manage.sh("pybabel init -i {} -d {} -l {}".format(
            messages_file,
            config.TEMP_DIR,
            locale,
        ))
        mo_file = join(locale_dir, 'LC_MESSAGES/messages.mo')
        assert not exists(mo_file)
        manage.translate_messages(args)
        assert exists(mo_file)
        mo = open(mo_file).read()
        assert 'code hello i18n' in mo
        assert 'template hello i18n' in mo

    def test_translate_messages_compile_arg(self):
        source = [
            join(self.dir, 'i18n/code.py'),
        ]
        kwargs = {
            'translations_dir': config.TEMP_DIR,
            'mapping': join(self.dir, 'i18n/babel.cfg'),
            'source': source,
            'extract_update': True,
            'compile': False,
            'verbose': logging.DEBUG,
            'version': version.__version__,
        }
        args = argparse.Namespace(**kwargs)
        manage.setup_verbosity(args)
        manage.translate_messages(args)
        messages_file = join(config.TEMP_DIR, 'messages.pot')
        assert exists(messages_file)
        pot = open(messages_file).read()
        assert 'code hello i18n' in pot

        locale = 'en_US'
        locale_dir = join(config.TEMP_DIR, locale)
        po_file = join(locale_dir, 'LC_MESSAGES/messages.po')
        manage.sh("pybabel init -i {} -d {} -l {}".format(
            messages_file,
            config.TEMP_DIR,
            locale,
        ))
        assert exists(po_file)
        # pretend this happened a few seconds ago
        few_seconds_ago = time.time() - 60
        os.utime(po_file, (few_seconds_ago, few_seconds_ago))

        mo_file = join(locale_dir, 'LC_MESSAGES/messages.mo')

        #
        # Extract+update but do not compile
        #
        old_po_mtime = getmtime(po_file)
        assert not exists(mo_file)
        manage.translate_messages(args)
        assert not exists(mo_file)
        current_po_mtime = getmtime(po_file)
        assert old_po_mtime < current_po_mtime

        #
        # Compile but do not extract+update
        #
        source = [
            join(self.dir, 'i18n/code.py'),
            join(self.dir, 'i18n/template.html'),
        ]
        kwargs['extract_update'] = False
        kwargs['compile'] = True
        args = argparse.Namespace(**kwargs)
        old_po_mtime = current_po_mtime
        manage.translate_messages(args)
        assert old_po_mtime == getmtime(po_file)
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
