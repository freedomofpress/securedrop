# -*- coding: utf-8 -*-

import argparse
import os
from os.path import abspath, dirname, exists, getmtime, join, realpath
os.environ['SECUREDROP_ENV'] = 'test'  # noqa
import logging
import i18n_tool
import pytest
import shutil
import subprocess
import time
import version


class TestI18NTool(object):

    def setup(self):
        self.dir = abspath(dirname(realpath(__file__)))

    def test_translate_desktop_l10n(self, tmpdir):
        in_files = {}
        for what in ('source', 'journalist'):
            in_files[what] = join(str(tmpdir), what + '.desktop.in')
            shutil.copy(join(self.dir, 'i18n/' + what + '.desktop.in'),
                        in_files[what])
        kwargs = {
            'translations_dir': str(tmpdir),
            'source': [in_files['source']],
            'extract_update': True,
            'compile': False,
            'verbose': logging.DEBUG,
            'version': version.__version__,
        }
        args = argparse.Namespace(**kwargs)
        i18n_tool.setup_verbosity(args)
        i18n_tool.translate_desktop(args)
        messages_file = join(str(tmpdir), 'desktop.pot')
        assert exists(messages_file)
        pot = open(messages_file).read()
        assert 'SecureDrop Source Interfaces' in pot
        # pretend this happened a few seconds ago
        few_seconds_ago = time.time() - 60
        os.utime(messages_file, (few_seconds_ago, few_seconds_ago))

        i18n_file = join(str(tmpdir), 'source.desktop')

        #
        # Extract+update but do not compile
        #
        kwargs['source'] = in_files.values()
        old_messages_mtime = getmtime(messages_file)
        assert not exists(i18n_file)
        i18n_tool.translate_desktop(args)
        assert not exists(i18n_file)
        current_messages_mtime = getmtime(messages_file)
        assert old_messages_mtime < current_messages_mtime

        locale = 'fr_FR'
        po_file = join(str(tmpdir), locale + ".po")
        i18n_tool.sh("""
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
        i18n_tool.translate_desktop(args)
        assert old_messages_mtime == getmtime(messages_file)
        po = open(po_file).read()
        assert 'SecureDrop Source Interfaces' in po
        assert 'SecureDrop Journalist Interfaces' not in po
        i18n = open(i18n_file).read()
        assert 'SOURCE FR' in i18n

    def test_translate_messages_l10n(self, tmpdir):
        source = [
            join(self.dir, 'i18n/code.py'),
            join(self.dir, 'i18n/template.html'),
        ]
        kwargs = {
            'translations_dir': str(tmpdir),
            'mapping': join(self.dir, 'i18n/babel.cfg'),
            'source': source,
            'extract_update': True,
            'compile': True,
            'verbose': logging.DEBUG,
            'version': version.__version__,
        }
        args = argparse.Namespace(**kwargs)
        i18n_tool.setup_verbosity(args)
        i18n_tool.translate_messages(args)
        messages_file = join(str(tmpdir), 'messages.pot')
        assert exists(messages_file)
        pot = open(messages_file).read()
        assert 'code hello i18n' in pot
        assert 'template hello i18n' in pot

        locale = 'en_US'
        locale_dir = join(str(tmpdir), locale)
        i18n_tool.sh("pybabel init -i {} -d {} -l {}".format(
            messages_file,
            str(tmpdir),
            locale,
        ))
        mo_file = join(locale_dir, 'LC_MESSAGES/messages.mo')
        assert not exists(mo_file)
        i18n_tool.translate_messages(args)
        assert exists(mo_file)
        mo = open(mo_file).read()
        assert 'code hello i18n' in mo
        assert 'template hello i18n' in mo

    def test_translate_messages_compile_arg(self, tmpdir):
        source = [
            join(self.dir, 'i18n/code.py'),
        ]
        kwargs = {
            'translations_dir': str(tmpdir),
            'mapping': join(self.dir, 'i18n/babel.cfg'),
            'source': source,
            'extract_update': True,
            'compile': False,
            'verbose': logging.DEBUG,
            'version': version.__version__,
        }
        args = argparse.Namespace(**kwargs)
        i18n_tool.setup_verbosity(args)
        i18n_tool.translate_messages(args)
        messages_file = join(str(tmpdir), 'messages.pot')
        assert exists(messages_file)
        pot = open(messages_file).read()
        assert 'code hello i18n' in pot

        locale = 'en_US'
        locale_dir = join(str(tmpdir), locale)
        po_file = join(locale_dir, 'LC_MESSAGES/messages.po')
        i18n_tool.sh("pybabel init -i {} -d {} -l {}".format(
            messages_file,
            str(tmpdir),
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
        i18n_tool.translate_messages(args)
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
        i18n_tool.translate_messages(args)
        assert old_po_mtime == getmtime(po_file)
        mo = open(mo_file).read()
        assert 'code hello i18n' in mo
        assert 'template hello i18n' not in mo


class TestSh(object):

    def test_sh(self):
        assert 'A' == i18n_tool.sh("echo -n A")
        with pytest.raises(Exception) as excinfo:
            i18n_tool.sh("exit 123")
        assert excinfo.value.returncode == 123

    def test_sh_progress(self, caplog):
        i18n_tool.sh("echo AB ; sleep 5 ; echo C")
        records = caplog.records
        assert ':sh: ' in records[0].message
        assert records[0].levelname == 'DEBUG'
        assert 'AB' == records[1].message
        assert records[1].levelname == 'DEBUG'
        assert 'C' == records[2].message
        assert records[2].levelname == 'DEBUG'

    def test_sh_input(self, caplog):
        assert 'abc' == i18n_tool.sh("cat", 'abc')

    def test_sh_fail(self, caplog):
        level = i18n_tool.log.getEffectiveLevel()
        i18n_tool.log.setLevel(logging.INFO)
        assert i18n_tool.log.getEffectiveLevel() == logging.INFO
        with pytest.raises(subprocess.CalledProcessError) as excinfo:
            i18n_tool.sh("echo AB ; echo C ; exit 111")
        i18n_tool.log.setLevel(level)
        assert excinfo.value.returncode == 111
        records = caplog.records
        assert 'AB' == records[0].message
        assert records[0].levelname == 'ERROR'
        assert 'C' == records[1].message
        assert records[1].levelname == 'ERROR'
