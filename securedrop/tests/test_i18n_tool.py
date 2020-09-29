# -*- coding: utf-8 -*-

import io
import os
from os.path import abspath, dirname, exists, getmtime, join, realpath
os.environ['SECUREDROP_ENV'] = 'test'  # noqa
import i18n_tool
from mock import patch
import pytest
import shutil
import signal
import time

from sh import sed, msginit, pybabel, git, touch


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
        with io.open(messages_file) as fobj:
            pot = fobj.read()
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
            '--sources', ",".join(list(in_files.values())),
            '--extract-update',
        ])
        assert not exists(i18n_file)
        current_messages_mtime = getmtime(messages_file)
        assert old_messages_mtime < current_messages_mtime

        locale = 'fr_FR'
        po_file = join(str(tmpdir), locale + ".po")
        msginit(
            '--no-translator',
            '--locale', locale,
            '--output', po_file,
            '--input', messages_file)
        source = 'SecureDrop Source Interfaces'
        sed('-i', '-e',
            '/{}/,+1s/msgstr ""/msgstr "SOURCE FR"/'.format(source),
            po_file)
        assert exists(po_file)

        # Regression test to trigger bug introduced when adding
        # Romanian as an accepted language.
        locale = 'ro'
        po_file = join(str(tmpdir), locale + ".po")
        msginit(
            '--no-translator',
            '--locale', locale,
            '--output', po_file,
            '--input', messages_file)
        source = 'SecureDrop Source Interfaces'
        sed('-i', '-e',
            '/{}/,+1s/msgstr ""/msgstr "SOURCE RO"/'.format(source),
            po_file)
        assert exists(po_file)

        #
        # Compile but do not extract+update
        #
        old_messages_mtime = current_messages_mtime
        i18n_tool.I18NTool().main([
            '--verbose',
            'translate-desktop',
            '--translations-dir', str(tmpdir),
            '--sources', ",".join(list(in_files.values()) + ['BOOM']),
            '--compile',
        ])
        assert old_messages_mtime == getmtime(messages_file)
        with io.open(po_file) as fobj:
            po = fobj.read()
            assert 'SecureDrop Source Interfaces' in po
            assert 'SecureDrop Journalist Interfaces' not in po
        with io.open(i18n_file) as fobj:
            i18n = fobj.read()
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
        with io.open(messages_file, 'rb') as fobj:
            pot = fobj.read()
            assert b'code hello i18n' in pot
            assert b'template hello i18n' in pot

        locale = 'en_US'
        locale_dir = join(str(tmpdir), locale)
        pybabel('init', '-i', messages_file, '-d', str(tmpdir), '-l', locale)
        mo_file = join(locale_dir, 'LC_MESSAGES/messages.mo')
        assert not exists(mo_file)
        i18n_tool.I18NTool().main(args)
        assert exists(mo_file)
        with io.open(mo_file, mode='rb') as fobj:
            mo = fobj.read()
            assert b'code hello i18n' in mo
            assert b'template hello i18n' in mo

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
        with io.open(messages_file) as fobj:
            pot = fobj.read()
            assert 'code hello i18n' in pot

        locale = 'en_US'
        locale_dir = join(str(tmpdir), locale)
        po_file = join(locale_dir, 'LC_MESSAGES/messages.po')
        pybabel(['init', '-i', messages_file, '-d', str(tmpdir), '-l', locale])
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
        with io.open(mo_file, mode='rb') as fobj:
            mo = fobj.read()
            assert b'code hello i18n' in mo
            assert b'template hello i18n' not in mo

    def test_require_git_email_name(self, tmpdir):
        k = {'_cwd': str(tmpdir)}
        git('init', **k)
        with pytest.raises(Exception) as excinfo:
            i18n_tool.I18NTool.require_git_email_name(str(tmpdir))
        assert 'please set name' in str(excinfo.value)

        git.config('user.email', "you@example.com", **k)
        git.config('user.name', "Your Name", **k)
        assert i18n_tool.I18NTool.require_git_email_name(str(tmpdir))

    def test_update_docs(self, tmpdir, caplog):
        k = {'_cwd': str(tmpdir)}
        git.init(**k)
        git.config('user.email', "you@example.com", **k)
        git.config('user.name', "Your Name", **k)
        os.makedirs(join(str(tmpdir), 'docs/includes'))
        touch('docs/includes/l10n.txt', **k)
        git.add('docs/includes/l10n.txt', **k)
        git.commit('-m', 'init', **k)

        i18n_tool.I18NTool().main([
            '--verbose',
            'update-docs',
            '--docs-repo-dir', str(tmpdir)])
        assert 'l10n.txt updated' in caplog.text
        caplog.clear()
        i18n_tool.I18NTool().main([
            '--verbose',
            'update-docs',
            '--docs-repo-dir', str(tmpdir)])
        assert 'l10n.txt already up to date' in caplog.text

    def test_update_from_weblate(self, tmpdir, caplog):
        d = str(tmpdir)
        for repo in ('i18n', 'securedrop'):
            os.mkdir(join(d, repo))
            k = {'_cwd': join(d, repo)}
            git.init(**k)
            git.config('user.email', 'you@example.com', **k)
            git.config('user.name',  'Loïc Nordhøy', **k)
            touch('README.md', **k)
            git.add('README.md', **k)
            git.commit('-m', 'README', 'README.md', **k)
        for o in os.listdir(join(self.dir, 'i18n')):
            f = join(self.dir, 'i18n', o)
            if os.path.isfile(f):
                shutil.copyfile(f, join(d, 'i18n', o))
            else:
                shutil.copytree(f, join(d, 'i18n', o))
        k = {'_cwd': join(d, 'i18n')}
        git.add('securedrop', 'install_files', **k)
        git.commit('-m', 'init', '-a', **k)
        git.checkout('-b', 'i18n', 'master', **k)

        def r():
            return "".join([str(l) for l in caplog.records])

        #
        # de_DE is not amount the supported languages, it is not taken
        # into account despite the fact that it exists in weblate.
        #
        caplog.clear()
        i18n_tool.I18NTool().main([
            '--verbose',
            'update-from-weblate',
            '--root', join(str(tmpdir), 'securedrop'),
            '--url', join(str(tmpdir), 'i18n'),
            '--supported-languages', 'nl',
        ])
        assert 'l10n: updated Dutch (nl)' in r()
        assert 'l10n: updated German (de_DE)' not in r()

        #
        # de_DE is added but there is no change in the nl translation
        # therefore nothing is done for nl
        #
        caplog.clear()
        i18n_tool.I18NTool().main([
            '--verbose',
            'update-from-weblate',
            '--root', join(str(tmpdir), 'securedrop'),
            '--url', join(str(tmpdir), 'i18n'),
            '--supported-languages', 'nl,de_DE',
        ])
        assert 'l10n: updated Dutch (nl)' not in r()
        assert 'l10n: updated German (de_DE)' in r()

        #
        # nothing new for nl or de_DE: nothing is done
        #
        caplog.clear()
        i18n_tool.I18NTool().main([
            '--verbose',
            'update-from-weblate',
            '--root', join(str(tmpdir), 'securedrop'),
            '--url', join(str(tmpdir), 'i18n'),
            '--supported-languages', 'nl,de_DE',
        ])
        assert 'l10n: updated Dutch (nl)' not in r()
        assert 'l10n: updated German (de_DE)' not in r()
        message = str(git('--no-pager', '-C', 'securedrop', 'show',
                          _cwd=d, _encoding='utf-8'))
        assert "Loïc" in message

        #
        # an update is done to nl in weblate
        #
        k = {'_cwd': join(d, 'i18n')}
        f = 'securedrop/translations/nl/LC_MESSAGES/messages.po'
        sed('-i', '-e', 's/inactiviteit/INACTIVITEIT/', f, **k)
        git.add(f, **k)
        git.config('user.email', 'somone@else.com', **k)
        git.config('user.name', 'Someone Else', **k)
        git.commit('-m', 'translation change', f, **k)

        k = {'_cwd': join(d, 'securedrop')}
        git.config('user.email', 'somone@else.com', **k)
        git.config('user.name', 'Someone Else', **k)

        #
        # the nl translation update from weblate is copied
        # over.
        #
        caplog.clear()
        i18n_tool.I18NTool().main([
            '--verbose',
            'update-from-weblate',
            '--root', join(str(tmpdir), 'securedrop'),
            '--url', join(str(tmpdir), 'i18n'),
            '--supported-languages', 'nl,de_DE',
        ])
        assert 'l10n: updated Dutch (nl)' in r()
        assert 'l10n: updated German (de_DE)' not in r()
        message = str(git('--no-pager', '-C', 'securedrop', 'show',
                          _cwd=d))
        assert "Someone Else" in message
        assert "Loïc" not in message
