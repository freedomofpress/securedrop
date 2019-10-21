#!/opt/venvs/securedrop-app-code/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse
import io
import logging
import os
import glob
import re
import signal
import subprocess
import sys
import textwrap
import version

from os.path import dirname, join, realpath

from sh import git, pybabel, sed, msgmerge, xgettext, msgfmt

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)


class I18NTool(object):

    #
    # The database of support language, indexed by the language code
    # used by weblate (i.e. whatever shows as CODE in
    # https://weblate.securedrop.org/projects/securedrop/securedrop/CODE/
    # is the index of the SUPPORTED_LANGUAGES database below.
    #
    # name: English name of the language to the documentation, not for
    #       display in the interface.
    # desktop: The language code used for dekstop icons.
    #
    SUPPORTED_LANGUAGES = {
        'ar': {'name': 'Arabic', 'desktop': 'ar', },
        'ca': {'name': 'Catalan', 'desktop': 'ca', },
        'cs': {'name': 'Czech', 'desktop': 'cs', },
        'de_DE': {'name': 'German', 'desktop': 'de_DE', },
        'el': {'name': 'Greek', 'desktop': 'el', },
        'es_ES': {'name': 'Spanish', 'desktop': 'es_ES', },
        'fr_FR': {'name': 'French', 'desktop': 'fr', },
        'hi': {'name': 'Hindi', 'desktop': 'hi', },
        'is': {'name': 'Icelandic', 'desktop': 'is', },
        'it_IT': {'name': 'Italian', 'desktop': 'it', },
        'nb_NO': {'name': 'Norwegian', 'desktop': 'nb_NO', },
        'nl': {'name': 'Dutch', 'desktop': 'nl', },
        'pt_BR': {'name': 'Portuguese, Brasil', 'desktop': 'pt_BR', },
        'ro': {'name': 'Romanian', 'desktop': 'ro', },
        'ru': {'name': 'Russian', 'desktop': 'ru', },
        'sk': {'name': 'Slovak', 'desktop': 'sk', },
        'sv': {'name': 'Swedish', 'desktop': 'sv', },
        'tr': {'name': 'Turkish', 'desktop': 'tr', },
        'zh_Hant': {'name': 'Chinese, Traditional', 'desktop': 'zh_Hant', },
    }

    def file_is_modified(self, path):
        dir = dirname(path)
        return subprocess.call(['git', '-C', dir, 'diff', '--quiet', path])

    def ensure_i18n_remote(self, args):
        k = {'_cwd': args.root}
        if b'i18n' not in git.remote(**k).stdout:
            git.remote.add('i18n', args.url, **k)
        git.fetch('i18n', **k)

    def translate_messages(self, args):
        messages_file = os.path.join(args.translations_dir, 'messages.pot')

        if args.extract_update:
            if not os.path.exists(args.translations_dir):
                os.makedirs(args.translations_dir)
            sources = args.sources.split(',')
            pybabel.extract(
                '--charset=utf-8',
                '--mapping', args.mapping,
                '--output', messages_file,
                '--project=SecureDrop',
                '--version', args.version,
                "--msgid-bugs-address=securedrop@freedom.press",
                "--copyright-holder=Freedom of the Press Foundation",
                *sources)
            sed('-i', '-e', '/^"POT-Creation-Date/d', messages_file)

            if (self.file_is_modified(messages_file) and
                    len(os.listdir(args.translations_dir)) > 1):
                tglob = '{}/*/LC_MESSAGES/*.po'.format(args.translations_dir)
                for translation in glob.iglob(tglob):
                    msgmerge('--previous', '--update', translation,
                             messages_file)
                log.warning("messages translations updated in {}".format(
                            messages_file))
            else:
                log.warning("messages translations are already up to date")

        if args.compile and len(os.listdir(args.translations_dir)) > 1:
            pybabel.compile('--directory', args.translations_dir)

    def translate_desktop(self, args):
        messages_file = os.path.join(args.translations_dir, 'desktop.pot')

        if args.extract_update:
            sources = args.sources.split(',')
            k = {'_cwd': args.translations_dir}
            xgettext(
                "--output=desktop.pot",
                "--language=Desktop",
                "--keyword",
                "--keyword=Name",
                "--package-version", args.version,
                "--msgid-bugs-address=securedrop@freedom.press",
                "--copyright-holder=Freedom of the Press Foundation",
                *sources,
                **k)
            sed('-i', '-e', '/^"POT-Creation-Date/d', messages_file, **k)

            if self.file_is_modified(messages_file):
                for f in os.listdir(args.translations_dir):
                    if not f.endswith('.po'):
                        continue
                    po_file = os.path.join(args.translations_dir, f)
                    msgmerge('--update', po_file, messages_file)
                log.warning("messages translations updated in " +
                            messages_file)
            else:
                log.warning("desktop translations are already up to date")

        if args.compile:
            pos = [f for f in os.listdir(args.translations_dir) if f.endswith('.po')]
            linguas = [l[:-3] for l in pos]
            content = "\n".join(linguas) + "\n"
            open(join(args.translations_dir, 'LINGUAS'), 'w').write(content)

            for source in args.sources.split(','):
                target = source.rstrip('.in')
                msgfmt('--desktop',
                       '--template', source,
                       '-o', target,
                       '-d', '.',
                       _cwd=args.translations_dir)

    def set_translate_parser(self,
                             subps,
                             parser,
                             translations_dir,
                             sources):
        parser.add_argument(
            '--extract-update',
            action='store_true',
            help=('extract strings to translate and '
                  'update existing translations'))
        parser.add_argument(
            '--compile',
            action='store_true',
            help='compile translations')
        parser.add_argument(
            '--translations-dir',
            default=translations_dir,
            help='Base directory for translation files (default {})'.format(
                translations_dir))
        parser.add_argument(
            '--version',
            default=version.__version__,
            help=('SecureDrop version '
                  'to store in pot files (default {})'.format(
                      version.__version__)))
        parser.add_argument(
            '--sources',
            default=sources,
            help='Source files and directories to extract (default {})'.format(
                sources))

    def set_translate_messages_parser(self, subps):
        parser = subps.add_parser('translate-messages',
                                  help=('Update and compile '
                                        'source and template translations'))
        translations_dir = join(dirname(realpath(__file__)), 'translations')
        sources = '.,source_templates,journalist_templates'
        self.set_translate_parser(subps, parser, translations_dir, sources)
        mapping = 'babel.cfg'
        parser.add_argument(
            '--mapping',
            default=mapping,
            help='Mapping of files to consider (default {})'.format(
                mapping))
        parser.set_defaults(func=self.translate_messages)

    def set_translate_desktop_parser(self, subps):
        parser = subps.add_parser('translate-desktop',
                                  help=('Update and compile '
                                        'desktop icons translations'))
        translations_dir = join(
            dirname(realpath(__file__)),
            '../install_files/ansible-base/roles/tails-config/templates')
        sources = 'desktop-journalist-icon.j2.in,desktop-source-icon.j2.in'
        self.set_translate_parser(subps, parser, translations_dir, sources)
        parser.set_defaults(func=self.translate_desktop)

    @staticmethod
    def require_git_email_name(git_dir):
        cmd = ('git -C {d} config --get user.name > /dev/null && '
               'git -C {d} config --get user.email > /dev/null'.format(
                   d=git_dir))
        if subprocess.call(cmd, shell=True):  # nosec
            if u'docker' in io.open('/proc/1/cgroup').read():
                log.error("remember ~/.gitconfig does not exist "
                          "in the dev-shell Docker container, "
                          "only .git/config does")
            raise Exception(cmd + ' returned false, please set name and email')
        return True

    def update_docs(self, args):
        l10n_content = u'.. GENERATED BY i18n_tool.py DO NOT EDIT:\n\n'
        for (code, info) in sorted(I18NTool.SUPPORTED_LANGUAGES.items()):
            l10n_content += '* ' + info['name'] + ' (``' + code + '``)\n'
        includes = join(args.documentation_dir, 'includes')
        l10n_txt = join(includes, 'l10n.txt')
        io.open(l10n_txt, mode='w').write(l10n_content)
        self.require_git_email_name(includes)
        if self.file_is_modified(l10n_txt):
            k = {'_cwd': includes}
            git.add('l10n.txt', **k)
            msg = 'docs: update the list of supported languages'
            git.commit('-m', msg, 'l10n.txt', **k)
            log.warning(l10n_txt + " updated")
            git_show_out = git.show(**k)
            log.warning(git_show_out)
        else:
            log.warning(l10n_txt + " already up to date")

    def set_update_docs_parser(self, subps):
        parser = subps.add_parser('update-docs',
                                  help=('Update the documentation'))
        documentation_dir = join(dirname(realpath(__file__)), '..', 'docs')
        parser.add_argument(
            '--documentation-dir',
            default=documentation_dir,
            help=('root directory of the SecureDrop documentation'
                  ' (default {})'.format(documentation_dir)))
        parser.set_defaults(func=self.update_docs)

    def update_from_weblate(self, args):
        self.ensure_i18n_remote(args)
        codes = list(I18NTool.SUPPORTED_LANGUAGES.keys())
        if args.supported_languages:
            codes = args.supported_languages.split(',')
        for code in sorted(codes):
            info = I18NTool.SUPPORTED_LANGUAGES[code]

            def need_update(p):
                exists = os.path.exists(join(args.root, p))
                k = {'_cwd': args.root}
                git.checkout('i18n/i18n', '--', p, **k)
                git.reset('HEAD', '--', p, **k)
                if not exists:
                    return True
                else:
                    return self.file_is_modified(join(args.root, p))

            def add(p):
                git('-C', args.root, 'add', p)

            updated = False
            #
            # Update messages
            #
            p = "securedrop/translations/{l}/LC_MESSAGES/messages.po".format(
                l=code)  # noqa: E741
            if need_update(p):
                add(p)
                updated = True
            #
            # Update desktop
            #
            desktop_code = info['desktop']
            p = join("install_files/ansible-base/roles",
                     "tails-config/templates/{l}.po".format(
                         l=desktop_code))  # noqa: E741
            if need_update(p):
                add(p)
                updated = True

            if updated:
                self.upstream_commit(args, code)

    def translators(self, args, path, commit_range):
        """
        Return the set of people who've modified a file in Weblate.

        Extracts all the authors of translation changes to the given
        path in the given commit range. Translation changes are
        identified by the presence of "Translated using Weblate" in
        the commit message.
        """
        translation_re = re.compile('Translated using Weblate')

        path_changes = git(
            '--no-pager', '-C', args.root,
            'log', '--format=%aN\x1e%s', commit_range, '--', path,
            _encoding='utf-8'
        )
        path_changes = u"{}".format(path_changes)
        path_changes = [c.split('\x1e') for c in path_changes.strip().split('\n')]
        path_changes = [c for c in path_changes if len(c) > 1 and translation_re.match(c[1])]

        path_authors = [c[0] for c in path_changes]
        return set(path_authors)

    def upstream_commit(self, args, code):
        self.require_git_email_name(args.root)
        authors = set()
        diffs = u"{}".format(git('--no-pager', '-C', args.root, 'diff', '--name-only', '--cached'))

        for path in sorted(diffs.strip().split('\n')):
            previous_message = u"{}".format(git(
                '--no-pager', '-C', args.root, 'log', '-n', '1', path,
                _encoding='utf-8'))
            update_re = re.compile(r'(?:updated from|  revision:) (\w+)')
            m = update_re.search(previous_message)
            if m:
                origin = m.group(1)
            else:
                origin = ''
            authors |= self.translators(args, path, '{}..i18n/i18n'.format(origin))

        authors = u"\n  ".join(sorted(authors))

        current = git('-C', args.root, 'rev-parse', 'i18n/i18n')
        info = I18NTool.SUPPORTED_LANGUAGES[code]
        message = textwrap.dedent(u"""
        l10n: updated {name} ({code})

        contributors:
          {authors}

        updated from:
          repo: {remote}
          revision: {current}
        """).format(
            remote=args.url,
            name=info['name'],
            authors=authors,
            code=code,
            current=current
        )
        git('-C', args.root, 'commit', '-m', message)

    def set_update_from_weblate_parser(self, subps):
        parser = subps.add_parser('update-from-weblate',
                                  help=('Import translations from weblate'))
        root = join(dirname(realpath(__file__)), '..')
        parser.add_argument(
            '--root',
            default=root,
            help=('root of the SecureDrop git repository'
                  ' (default {})'.format(root)))
        url = 'https://github.com/freedomofpress/securedrop-i18n'
        parser.add_argument(
            '--url',
            default=url,
            help=('URL of the weblate repository'
                  ' (default {})'.format(url)))
        parser.add_argument(
            '--supported-languages',
            help='comma separated list of supported languages')
        parser.set_defaults(func=self.update_from_weblate)

    def set_list_locales_parser(self, subps):
        parser = subps.add_parser('list-locales', help='List supported locales')
        parser.set_defaults(func=self.list_locales)

    def list_locales(self, args):
        print(sorted(list(self.SUPPORTED_LANGUAGES.keys()) + ['en_US']))

    def set_list_translators_parser(self, subps):
        parser = subps.add_parser('list-translators',
                                  help=('List contributing translators'))
        root = join(dirname(realpath(__file__)), '..')
        parser.add_argument(
            '--root',
            default=root,
            help=('root of the SecureDrop git repository'
                  ' (default {})'.format(root)))
        url = 'https://github.com/freedomofpress/securedrop-i18n'
        parser.add_argument(
            '--url',
            default=url,
            help=('URL of the weblate repository'
                  ' (default {})'.format(url)))
        parser.add_argument(
            '--all',
            action="store_true",
            help=(
                "List everyone who's ever contributed, instead of just since the last "
                "sync from Weblate."
            )
        )
        parser.set_defaults(func=self.list_translators)

    def get_last_sync(self):
        commits = git('--no-pager', 'log', '--format=%h:%s', 'i18n/i18n', _encoding='utf-8')
        for commit in commits:
            commit_hash, msg = commit.split(':', 1)
            if msg.startswith("l10n: sync "):
                return commit_hash
        return ""

    def list_translators(self, args):
        self.ensure_i18n_remote(args)
        app_template = "securedrop/translations/{}/LC_MESSAGES/messages.po"
        desktop_template = "install_files/ansible-base/roles/tails-config/templates/{}.po"
        last_sync = self.get_last_sync()
        for code, info in sorted(I18NTool.SUPPORTED_LANGUAGES.items()):
            translators = set([])
            paths = [
                app_template.format(code),
                desktop_template.format(info["desktop"]),
            ]
            for path in paths:
                try:
                    commit_range = "i18n/i18n"
                    if last_sync and not args.all:
                        commit_range = '{}..{}'.format(last_sync, commit_range)
                    t = self.translators(args, path, commit_range)
                    translators.update(t)
                except Exception as e:
                    print("Could not check git history of {}: {}".format(path, e), file=sys.stderr)
            print(u"{} ({}):\n  {}".format(code, info["name"], "\n  ".join(sorted(translators))))

    def get_args(self):
        parser = argparse.ArgumentParser(
            prog=__file__,
            description='i18n tool for SecureDrop.')
        parser.add_argument('-v', '--verbose', action='store_true')
        subps = parser.add_subparsers()

        self.set_translate_messages_parser(subps)
        self.set_translate_desktop_parser(subps)
        self.set_update_docs_parser(subps)
        self.set_update_from_weblate_parser(subps)
        self.set_list_translators_parser(subps)
        self.set_list_locales_parser(subps)

        return parser

    def setup_verbosity(self, args):
        if args.verbose:
            logging.getLogger('sh.command').setLevel(logging.INFO)
            log.setLevel(logging.DEBUG)
        else:
            log.setLevel(logging.INFO)

    def main(self, argv):
        try:
            args = self.get_args().parse_args(argv)
            self.setup_verbosity(args)
            return args.func(args)
        except KeyboardInterrupt:
            return signal.SIGINT


if __name__ == '__main__':  # pragma: no cover
    sys.exit(I18NTool().main(sys.argv[1:]))
