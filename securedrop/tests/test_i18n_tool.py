# -*- coding: utf-8 -*-

import os
from os.path import abspath, dirname, exists, getmtime, join, realpath
os.environ['SECUREDROP_ENV'] = 'test'  # noqa
import logging
import i18n_tool
from mock import patch
import pytest
import shutil
import signal
import subprocess
import time


class TestI18NTool(object):

    def setup(self):
        self.dir = abspath(dirname(realpath(__file__)))

    def test_main(self, tmpdir, caplog):
        with pytest.raises(SystemExit):
            i18n_tool.I18NTool().main(['--help'])

        tool = i18n_tool.I18NTool()
        with patch.object(tool,
                          'setup_verbosity',
                          side_effect=KeyboardInterrupt):
            assert tool.main([
                'translate-messages',
                '--translations-dir', str(tmpdir)
            ]) == signal.SIGINT

        assert tool.main([
            'translate-messages',
            '--translations-dir', str(tmpdir),
            '--extract-update'
        ]) is None
        assert 'pybabel extract' not in caplog.text

        assert tool.main([
            '--verbose',
            'translate-messages',
            '--translations-dir', str(tmpdir),
            '--extract-update'
        ]) is None
        assert 'pybabel extract' in caplog.text

    def test_translate_desktop_l10n(self, tmpdir):
        in_files = {}
        for what in ('source', 'journalist'):
            in_files[what] = join(str(tmpdir), what + '.desktop.in')
            shutil.copy(join(self.dir, 'i18n/' + what + '.desktop.in'),
                        in_files[what])
        i18n_tool.I18NTool().main([
            '--verbose',
            'translate-desktop',
            '--translations-dir', str(tmpdir),
            '--sources', in_files['source'],
            '--extract-update',
        ])
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
        old_messages_mtime = getmtime(messages_file)
        assert not exists(i18n_file)
        i18n_tool.I18NTool().main([
            '--verbose',
            'translate-desktop',
            '--translations-dir', str(tmpdir),
            '--sources', ",".join(in_files.values()),
            '--extract-update',
        ])
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
        old_messages_mtime = current_messages_mtime
        i18n_tool.I18NTool().main([
            '--verbose',
            'translate-desktop',
            '--translations-dir', str(tmpdir),
            '--sources', ",".join(in_files.values() + ['BOOM']),
            '--compile',
        ])
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
        args = [
            '--verbose',
            'translate-messages',
            '--translations-dir', str(tmpdir),
            '--mapping', join(self.dir, 'i18n/babel.cfg'),
            '--sources', ",".join(source),
            '--extract-update',
            '--compile',
        ]
        i18n_tool.I18NTool().main(args)
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
        i18n_tool.I18NTool().main(args)
        assert exists(mo_file)
        mo = open(mo_file).read()
        assert 'code hello i18n' in mo
        assert 'template hello i18n' in mo

    def test_translate_messages_compile_arg(self, tmpdir):
        args = [
            '--verbose',
            'translate-messages',
            '--translations-dir', str(tmpdir),
            '--mapping', join(self.dir, 'i18n/babel.cfg'),
        ]
        i18n_tool.I18NTool().main(args + [
            '--sources', join(self.dir, 'i18n/code.py'),
            '--extract-update',
        ])
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
        i18n_tool.I18NTool().main(args + [
            '--sources', join(self.dir, 'i18n/code.py'),
            '--extract-update',
        ])
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
        old_po_mtime = current_po_mtime
        i18n_tool.I18NTool().main(args + [
            '--sources', ",".join(source),
            '--compile',
        ])
        assert old_po_mtime == getmtime(po_file)
        mo = open(mo_file).read()
        assert 'code hello i18n' in mo
        assert 'template hello i18n' not in mo

    def test_update_docs(self, tmpdir, caplog):
        os.makedirs(join(str(tmpdir), 'includes'))
        i18n_tool.sh("""
        cd {dir}
        git init
        git config user.email "you@example.com"
        git config user.name "Your Name"
        mkdir includes
        touch includes/l10n.txt
        git add includes/l10n.txt
        git commit -m 'init'
        """.format(dir=str(tmpdir)))
        i18n_tool.I18NTool().main([
            '--verbose',
            'update-docs',
            '--documentation-dir', str(tmpdir)])
        assert 'l10n.txt updated' in caplog.text
        caplog.clear()
        i18n_tool.I18NTool().main([
            '--verbose',
            'update-docs',
            '--documentation-dir', str(tmpdir)])
        assert 'l10n.txt already up to date' in caplog.text


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
