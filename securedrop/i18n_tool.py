#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import logging
import os
import re
import signal
import subprocess
import sys
import tempfile
import textwrap
import version

from twisted.internet import reactor
import scrapy
from scrapy.crawler import Crawler
from scrapy import signals

from os.path import dirname, join, realpath

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)


def sh(command, input=None):
    """Run the *command* which must be a shell snippet. The stdin is
    either /dev/null or the *input* argument string.

    The stderr/stdout of the snippet are captured and logged via
    logging.debug(), one line at a time.
    """
    log.debug(":sh: " + command)
    if input is None:
        stdin = None
    else:
        stdin = subprocess.PIPE
    proc = subprocess.Popen(
        args=command,
        stdin=stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        bufsize=1)
    if stdin is not None:
        proc.stdin.write(input)
        proc.stdin.close()
    lines_of_command_output = []
    loggable_line_list = []
    with proc.stdout:
        for line in iter(proc.stdout.readline, b''):
            line = line.decode('utf-8')
            lines_of_command_output.append(line)
            loggable_line = line.strip().encode('ascii', 'ignore')
            log.debug(loggable_line)
            loggable_line_list.append(loggable_line)
    if proc.wait() != 0:
        if log.getEffectiveLevel() > logging.DEBUG:
            for loggable_line in loggable_line_list:
                log.error(loggable_line)
        raise subprocess.CalledProcessError(
            returncode=proc.returncode,
            cmd=command
        )
    return "".join(lines_of_command_output)


class WeblateSpider(scrapy.Spider):
    handle_httpstatus_list = [404, 500]

    name = "weblate"

    custom_settings = {
        'RETRY_ENABLED': False,
        'EXTENSIONS': {
            'scrapy.extensions.telnet.TelnetConsole': None,
            'scrapy.extensions.memusage.MemoryUsage': None,
            'scrapy.extensions.logstats.LogStats': None,
            'scrapy.extensions.corestats.CoreStats': None,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.stats.DownloaderStats': None,
        },
        'ITEM_PIPELINES': {
            'i18n_tool.JsonMailWriterPipeline': 800,
        }
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(WeblateSpider, cls).from_crawler(crawler,
                                                        *args,
                                                        **kwargs)
        crawler.signals.connect(spider.spider_error,
                                signal=signals.spider_error)
        spider.failed = False
        return spider

    def spider_error(self, failure, response, spider):
        self.failed = True

    def start_requests(self):
        yield scrapy.Request(self.url + '/accounts/login/',
                             callback=self.login)

    def login(self, response):
        return scrapy.FormRequest.from_response(
            response,
            formdata={
                'username': self.username,
                'password': self.password
            },
            callback=self.after_login)

    def after_login(self, response):
        assert response.css('#profile-button')
        return scrapy.Request(
            url=self.url + '/admin/auth/user/',
            callback=self.user_list)

    def user_list(self, response):
        next_page = response.xpath(
            '//a[@title="Localizationlab"]/@href').extract_first()
        return response.follow(next_page, self.localizationlab_list)

    def localizationlab_list(self, response):
        for mail in response.css('.field-email::text').extract():
            yield {'email': mail}


class JsonMailWriterPipeline(object):

    def open_spider(self, spider):
        self.emails = []

    def close_spider(self, spider):
        open(spider.filename, 'w').write(" ".join(self.emails))

    def process_item(self, item, spider):
        self.emails.append(item['email'])
        return item


class I18NTool(object):

    #
    # The database of support language, indexed by the language code
    # used by weblate (i.e. whatever shows as CODE in
    # https://weblate.securedrop.club/projects/securedrop/securedrop/CODE/
    # is the index of the SUPPORTED_LANGUAGES database below.
    #
    # name: English name of the language to the documentation, not for
    #       display in the interface.
    # desktop: The language code used for dekstop icons.
    #
    SUPPORTED_LANGUAGES = {
        'ar': {'name': 'Arabic', 'desktop': 'ar', },
        'de_DE': {'name': 'German', 'desktop': 'de_DE', },
        'es_ES': {'name': 'Spanish', 'desktop': 'es_ES', },
        'fr_FR': {'name': 'French', 'desktop': 'fr', },
        'it_IT': {'name': 'Italian', 'desktop': 'it', },
        'nb_NO': {'name': 'Norwegian', 'desktop': 'nb_NO', },
        'nl': {'name': 'Dutch', 'desktop': 'nl', },
        'pt_BR': {'name': 'Portuguese, Brasil', 'desktop': 'pt_BR', },
        'tr': {'name': 'Turkish', 'desktop': 'tr', },
        'zh_Hant': {'name': 'Chinese, Traditional', 'desktop': 'zh_Hant', },
    }

    def file_is_modified(self, path):
        dir = dirname(path)
        return subprocess.call(['git', '-C', dir, 'diff', '--quiet', path])

    def ensure_i18n_remote(self, args):
        sh("""
        set -ex
        cd {root}
        if ! git remote | grep --quiet i18n ; then
           git remote add i18n {url}
        fi
        git fetch i18n
        """.format(root=args.securedrop_root,
                   url=args.weblate_git_url))

    def translate_messages(self, args):
        messages_file = os.path.join(args.translations_dir, 'messages.pot')

        if args.extract_update:
            sh("""
            set -xe

            mkdir -p {translations_dir}

            pybabel extract \
            --charset=utf-8 \
            --mapping={mapping} \
            --output={messages_file} \
            --project=SecureDrop \
            --version={version} \
            --msgid-bugs-address='securedrop@freedom.press' \
            --copyright-holder='Freedom of the Press Foundation' \
            {sources}

            # remove this line so the file does not change if no
            # strings are modified
            sed -i '/^"POT-Creation-Date/d' {messages_file}
            """.format(translations_dir=args.translations_dir,
                       mapping=args.mapping,
                       messages_file=messages_file,
                       version=args.version,
                       sources=" ".join(args.sources.split(','))))

            if (self.file_is_modified(messages_file) and
                    len(os.listdir(args.translations_dir)) > 1):
                sh("""
                set -xe
                for translation in {translations_dir}/*/LC_MESSAGES/*.po ; do
                  msgmerge --previous --update $translation {messages_file}
                done
                """.format(translations_dir=args.translations_dir,
                           messages_file=messages_file))
                log.warning("messages translations updated in " +
                            messages_file)
            else:
                log.warning("messages translations are already up to date")

        if args.compile and len(os.listdir(args.translations_dir)) > 1:
            sh("""
            set -x
            pybabel compile --directory {translations_dir}
            """.format(translations_dir=args.translations_dir))

    def translate_desktop(self, args):
        messages_file = os.path.join(args.translations_dir, 'desktop.pot')

        if args.extract_update:
            sh("""
            set -xe
            cd {translations_dir}
            xgettext \
               --output=desktop.pot \
               --language=Desktop \
               --keyword \
               --keyword=Name \
               --package-version={version} \
               --msgid-bugs-address='securedrop@freedom.press' \
               --copyright-holder='Freedom of the Press Foundation' \
               {sources}

            # remove this line so the file does not change if no
            # strings are modified
            sed -i '/^"POT-Creation-Date/d' {messages_file}
            """.format(translations_dir=args.translations_dir,
                       messages_file=messages_file,
                       version=args.version,
                       sources=" ".join(args.sources.split(','))))

            if self.file_is_modified(messages_file):
                for f in os.listdir(args.translations_dir):
                    if not f.endswith('.po'):
                        continue
                    po_file = os.path.join(args.translations_dir, f)
                    sh("""
                    msgmerge --update {po_file} {messages_file}
                    """.format(po_file=po_file,
                               messages_file=messages_file))
                log.warning("messages translations updated in " +
                            messages_file)
            else:
                log.warning("desktop translations are already up to date")

        if args.compile:
            sh("""
            set -ex
            cd {translations_dir}
            find *.po | sed -e 's/\.po$//' > LINGUAS
            for source in {sources} ; do
               target=$(basename $source .in)
               msgfmt --desktop --template $source -o $target -d .
            done
            """.format(translations_dir=args.translations_dir,
                       sources=" ".join(args.sources.split(','))))

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
        if subprocess.call(cmd, shell=True):  #  nosec
            raise Exception(cmd + ' returned false, please set name and email')
        return True

    def update_docs(self, args):
        l10n_content = '.. GENERATED BY i18n_tool.py DO NOT EDIT:\n\n'
        for (code, info) in sorted(I18NTool.SUPPORTED_LANGUAGES.items()):
            l10n_content += '* ' + info['name'] + ' (' + code + ')\n'
        includes = join(args.documentation_dir, 'includes')
        l10n_txt = join(includes, 'l10n.txt')
        open(l10n_txt, 'w').write(l10n_content)
        self.require_git_email_name(includes)
        if self.file_is_modified(l10n_txt):
            sh("""
            set -ex
            cd {includes}
            git add l10n.txt
            git commit \
              -m 'docs: update the list of supported languages' \
              l10n.txt
            """.format(includes=includes))
            log.warning(l10n_txt + " updated")
            log.warning(sh("cd " + includes + "; git show"))
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
        codes = I18NTool.SUPPORTED_LANGUAGES.keys()
        if args.supported_languages:
            codes = args.supported_languages.split(',')
        for code in codes:
            info = I18NTool.SUPPORTED_LANGUAGES[code]

            def need_update(p):
                exists = os.path.exists(join(args.securedrop_root, p))
                sh("""
                set -ex
                cd {r}
                git checkout i18n/i18n -- {p}
                git reset HEAD -- {p}
                """.format(r=args.securedrop_root, p=p))
                if not exists:
                    return True
                else:
                    return self.file_is_modified(join(args.securedrop_root, p))

            def add(p):
                sh("git -C {r} add {p}".format(r=args.securedrop_root, p=p))
            updated = False
            #
            # Update messages
            #
            p = "securedrop/translations/{l}/LC_MESSAGES/messages.po".format(
                l=code)
            if need_update(p):
                add(p)
                updated = True
            #
            # Update desktop
            #
            desktop_code = info['desktop']
            p = join("install_files/ansible-base/roles",
                     "tails-config/templates/{l}.po".format(
                         l=desktop_code))
            if need_update(p):
                add(p)
                updated = True

            if updated:
                self.upstream_commit(args, code)

    def upstream_commit(self, args, code):
        self.require_git_email_name(args.securedrop_root)
        authors = set()
        for path in sh("git -C {r} diff --name-only --cached".format(
                r=args.securedrop_root)).split():
            previous_message = sh("git -C {r} log -n 1 {p}".format(
                r=args.securedrop_root, p=path))
            m = re.search('copied from (\w+)', previous_message)
            if m:
                origin = m.group(1)
            else:
                origin = ''
            authors |= set(sh("""
            git -C {r} log --format=%aN {o}..i18n/i18n -- {p}
            """.format(r=args.securedrop_root,
                       o=origin,
                       p=path)).strip().split('\n'))
        current = sh("git -C {r} rev-parse i18n/i18n".format(
            r=args.securedrop_root)).strip()
        info = I18NTool.SUPPORTED_LANGUAGES[code]
        message = textwrap.dedent(u"""
        l10n: updated {code} {name}

        localizers: {authors}

        {remote}
        copied from {current}
        """.format(remote=args.weblate_git_url,
                   name=info['name'],
                   authors=", ".join(authors),
                   code=code,
                   current=current))
        sh(u'git -C {r} commit -m "{message}"'.format(
            r=args.securedrop_root,
            message=message.replace('"', '\"')).encode('utf-8'))

    def set_supported_languages_parser(self, parser):
        root = join(dirname(realpath(__file__)), '..')
        parser.add_argument(
            '--securedrop-root',
            default=root,
            help=('root of the SecureDrop git repository'
                  ' (default {})'.format(root)))
        url = 'https://lab.securedrop.club/bot/securedrop.git'
        parser.add_argument(
            '--weblate-git-url',
            default=url,
            help=('URL of the weblate repository'
                  ' (default {})'.format(url)))
        parser.add_argument(
            '--supported-languages',
            help='comma separated list of supported languages')

    def set_update_from_weblate_parser(self, subps):
        parser = subps.add_parser('update-from-weblate',
                                  help=('Import translations from weblate'))
        self.set_supported_languages_parser(parser)
        parser.set_defaults(func=self.update_from_weblate)

    def credits(self, args):
        with tempfile.NamedTemporaryFile() as f:
            runner = Crawler(WeblateSpider)
            d = runner.crawl(username=args.username,
                             password=args.password,
                             url=args.weblate_url,
                             filename=f.name)
            d.addBoth(lambda _: reactor.stop())
            reactor.run()
            assert not runner.spider.failed
            print(open(f.name).read())

    def set_weblate_parser(self, parser):
        parser.add_argument(
            '--username',
            required=True,
            help='weblate username')
        parser.add_argument(
            '--password',
            required=True,
            help='weblate password')
        url = 'https://weblate.securedrop.club'
        parser.add_argument(
            '--weblate-url',
            default=url,
            help='weblate URL (default: {})'.format(url))

    def set_credits_parser(self, subps):
        parser = subps.add_parser('credits',
                                  help=('Display localizers credits'))
        self.set_supported_languages_parser(parser)
        self.set_weblate_parser(parser)
        parser.set_defaults(func=self.credits)

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
        self.set_credits_parser(subps)

        return parser

    def setup_verbosity(self, args):
        if args.verbose:
            logging.getLogger('scrapy').setLevel(logging.DEBUG)
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
