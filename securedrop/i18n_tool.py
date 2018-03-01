#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import os
import signal
import subprocess
import sys
import version

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


def translate_messages(args):
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
                   sources=" ".join(args.source)))

        changed = subprocess.call("git diff --quiet {}".format(messages_file),
                                  shell=True)  # nosec

        if changed and len(os.listdir(args.translations_dir)) > 1:
            sh("""
            set -xe
            for translation in {translations_dir}/*/LC_MESSAGES/*.po ; do
              msgmerge --previous --update $translation {messages_file}
            done
            """.format(translations_dir=args.translations_dir,
                       messages_file=messages_file))
            log.warning("messages translations updated in " + messages_file)
        else:
            log.warning("messages translations are already up to date")

    if args.compile and len(os.listdir(args.translations_dir)) > 1:
        sh("""
        set -x
        pybabel compile --directory {translations_dir}
        """.format(translations_dir=args.translations_dir))


def translate_desktop(args):
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
                   sources=" ".join(args.source)))

        changed = subprocess.call("git diff --quiet {}".format(messages_file),
                                  shell=True)  # nosec

        if changed:
            for f in os.listdir(args.translations_dir):
                if not f.endswith('.po'):
                    continue
                po_file = os.path.join(args.translations_dir, f)
                sh("""
                msgmerge --update {po_file} {messages_file}
                """.format(po_file=po_file,
                           messages_file=messages_file))
            log.warning("messages translations updated in " + messages_file)
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
                   sources=" ".join(args.source)))


def get_args():
    parser = argparse.ArgumentParser(prog=__file__, description='i18n tool '
                                     'for SecureDrop.')
    parser.add_argument('-v', '--verbose', action='store_true')
    subps = parser.add_subparsers()

    set_translate_messages_parser(subps)
    set_translate_desktop_parser(subps)

    return parser


def set_translate_parser(subps,
                         parser,
                         translations_dir,
                         sources):
    parser.add_argument(
        '--extract-update',
        action='store_true',
        help='extract strings to translate and update existing translations')
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
        help='SecureDrop version to store in pot files (default {})'.format(
            version.__version__))
    parser.add_argument(
        '--source',
        default=sources,
        action='append',
        help='Source files and directories to extract (default {})'.format(
            sources))


def set_translate_messages_parser(subps):
    parser = subps.add_parser('translate-messages',
                              help=('Update and compile '
                                    'source and template translations'))
    translations_dir = join(dirname(realpath(__file__)), 'translations')
    sources = ['.', 'source_templates', 'journalist_templates']
    set_translate_parser(subps, parser, translations_dir, sources)
    mapping = 'babel.cfg'
    parser.add_argument(
        '--mapping',
        default=mapping,
        help='Mapping of files to consider (default {})'.format(
            mapping))
    parser.set_defaults(func=translate_messages)


def set_translate_desktop_parser(subps):
    parser = subps.add_parser('translate-desktop',
                              help=('Update and compile '
                                    'desktop icons translations'))
    translations_dir = join(
        dirname(realpath(__file__)),
        '../install_files/ansible-base/roles/tails-config/templates')
    sources = ['desktop-journalist-icon.j2.in', 'desktop-source-icon.j2.in']
    set_translate_parser(subps, parser, translations_dir, sources)
    parser.set_defaults(func=translate_desktop)


def setup_verbosity(args):
    if args.verbose:
        logging.getLogger(__name__).setLevel(logging.DEBUG)
    else:
        logging.getLogger(__name__).setLevel(logging.INFO)


def _run_from_commandline():  # pragma: no cover
    try:
        args = get_args().parse_args()
        setup_verbosity(args)
        rc = args.func(args)
        sys.exit(rc)
    except KeyboardInterrupt:
        sys.exit(signal.SIGINT)


if __name__ == '__main__':  # pragma: no cover
    _run_from_commandline()
