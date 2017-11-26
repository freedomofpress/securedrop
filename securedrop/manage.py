#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import codecs
import logging
import os
import shutil
import signal
import subprocess
import sys
import time
import traceback
import version

import qrcode
from sqlalchemy.orm.exc import NoResultFound

os.environ['SECUREDROP_ENV'] = 'dev'  # noqa
import config
import crypto_util
from db import (db_session, init_db, Journalist, PasswordError,
                InvalidUsernameException)
from management.run import run

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


def reset(args):
    """Clears the SecureDrop development applications' state, restoring them to
    the way they were immediately after running `setup_dev.sh`. This command:
    1. Erases the development sqlite database file.
    2. Regenerates the database.
    3. Erases stored submissions and replies from the store dir.
    """
    # Erase the development db file
    if not hasattr(config, 'DATABASE_FILE'):
        raise Exception("TODO: ./manage.py doesn't know how to clear the db "
                        'if the backend is not sqlite')
    try:
        os.remove(config.DATABASE_FILE)
    except OSError:
        pass

    # Regenerate the database
    init_db()

    # Clear submission/reply storage
    try:
        os.stat(config.STORE_DIR)
    except OSError:
        pass
    else:
        for source_dir in os.listdir(config.STORE_DIR):
            try:
                # Each entry in STORE_DIR is a directory corresponding
                # to a source
                shutil.rmtree(os.path.join(config.STORE_DIR, source_dir))
            except OSError:
                pass
    return 0


def add_admin(args):
    return _add_user(is_admin=True)


def add_journalist(args):
    return _add_user()


def _get_username():
    while True:
        username = raw_input('Username: ')
        try:
            Journalist.check_username_acceptable(username)
        except InvalidUsernameException as e:
            print('Invalid username: ' + str(e))
        else:
            return username


def _get_yubikey_usage():
    '''Function used to allow for test suite mocking'''
    while True:
        answer = raw_input('Will this user be using a YubiKey [HOTP]? '
                           '(y/N): ').lower().strip()
        if answer in ('y', 'yes'):
            return True
        elif answer in ('', 'n', 'no'):
            return False
        else:
            print 'Invalid answer. Please type "y" or "n"'


def _make_password():
    while True:
        password = crypto_util.genrandomid(7)
        try:
            Journalist.check_password_acceptable(password)
            return password
        except PasswordError:
            continue


def _add_user(is_admin=False):
    username = _get_username()

    print("Note: Passwords are now autogenerated.")
    password = _make_password()
    print("This user's password is: {}".format(password))

    is_hotp = _get_yubikey_usage()
    otp_secret = None
    if is_hotp:
        while True:
            otp_secret = raw_input(
                "Please configure this user's YubiKey and enter the secret: ")
            if otp_secret:
                tmp_str = otp_secret.replace(" ", "")
                if len(tmp_str) != 40:
                    print("The length of the secret is not correct. "
                          "Expected 40 characters, but received {0}. "
                          "Try again.".format(len(tmp_str)))
                    continue
            if otp_secret:
                break

    try:
        user = Journalist(username=username,
                          password=password,
                          is_admin=is_admin,
                          otp_secret=otp_secret)
        db_session.add(user)
        db_session.commit()
    except Exception as exc:
        db_session.rollback()
        if "UNIQUE constraint failed: journalists.username" in str(exc):
            print('ERROR: That username is already taken!')
        else:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print(repr(traceback.format_exception(exc_type, exc_value,
                                                  exc_traceback)))
        return 1
    else:
        print('User "{}" successfully added'.format(username))
        if not otp_secret:
            # Print the QR code for FreeOTP/ Google Authenticator
            print('\nScan the QR code below with FreeOTP or Google '
                  'Authenticator:\n')
            uri = user.totp.provisioning_uri(username,
                                             issuer_name='SecureDrop')
            qr = qrcode.QRCode()
            qr.add_data(uri)
            sys.stdout = codecs.getwriter("utf-8")(sys.stdout)
            qr.print_ascii(tty=sys.stdout.isatty())
            print('\nIf the barcode does not render correctly, try changing '
                  "your terminal's font (Monospace for Linux, Menlo for OS "
                  'X). If you are using iTerm on Mac OS X, you will need to '
                  'change the "Non-ASCII Font", which is your profile\'s Text '
                  "settings.\n\nCan't scan the barcode? Enter following "
                  'shared secret '
                  'manually:\n{}\n'.format(user.formatted_otp_secret))
        return 0


def _get_username_to_delete():
    return raw_input('Username to delete: ')


def _get_delete_confirmation(user):
    confirmation = raw_input('Are you sure you want to delete user '
                             '"{}" (y/n)?'.format(user))
    if confirmation.lower() != 'y':
        print('Confirmation not received: user "{}" was NOT '
              'deleted'.format(user))
        return False
    return True


def delete_user(args):
    """Deletes a journalist or administrator from the application."""
    username = _get_username_to_delete()
    try:
        selected_user = Journalist.query.filter_by(username=username).one()
    except NoResultFound:
        print('ERROR: That user was not found!')
        return 0

    # Confirm deletion if user is found
    if not _get_delete_confirmation(selected_user.username):
        return 0

    # Try to delete user from the database
    try:
        db_session.delete(selected_user)
        db_session.commit()
    except Exception as e:
        # If the user was deleted between the user selection and confirmation,
        # (e.g., through the web app), we don't report any errors. If the user
        # is still there, but there was a error deleting them from the
        # database, we do report it.
        try:
            Journalist.query.filter_by(username=username).one()
        except NoResultFound:
            pass
        else:
            raise e

    print('User "{}" successfully deleted'.format(username))
    return 0


def clean_tmp(args):  # pragma: no cover
    """Cleanup the SecureDrop temp directory. """
    if not os.path.exists(args.directory):
        log.debug('{} does not exist, do nothing'.format(args.directory))
        return 0

    def listdir_fullpath(d):
        return [os.path.join(d, f) for f in os.listdir(d)]

    too_old = args.days * 24 * 60 * 60
    for path in listdir_fullpath(args.directory):
        if time.time() - os.stat(path).st_mtime > too_old:
            os.remove(path)
            log.debug('{} removed'.format(path))
        else:
            log.debug('{} modified less than {} days ago'.format(
                path, args.days))

    return 0


def translate(args):
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
                                  shell=True)

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


def get_args():
    parser = argparse.ArgumentParser(prog=__file__, description='Management '
                                     'and testing utility for SecureDrop.')
    parser.add_argument('-v', '--verbose', action='store_true')
    subps = parser.add_subparsers()
    # Run WSGI app
    run_subp = subps.add_parser('run', help='Run the Werkzeug source & '
                                'journalist WSGI apps. WARNING!!! For '
                                'development only, not to be used in '
                                'production.')
    run_subp.set_defaults(func=run)
    # Add/remove journalists + admins
    admin_subp = subps.add_parser('add-admin', help='Add an admin to the '
                                  'application.')
    admin_subp.set_defaults(func=add_admin)
    admin_subp_a = subps.add_parser('add_admin', help='^')
    admin_subp_a.set_defaults(func=add_admin)
    journalist_subp = subps.add_parser('add-journalist', help='Add a '
                                       'journalist to the application.')
    journalist_subp.set_defaults(func=add_journalist)
    journalist_subp_a = subps.add_parser('add_journalist', help='^')
    journalist_subp_a.set_defaults(func=add_journalist)
    delete_user_subp = subps.add_parser('delete-user', help='Delete a user '
                                        'from the application.')
    delete_user_subp.set_defaults(func=delete_user)
    delete_user_subp_a = subps.add_parser('delete_user', help='^')
    delete_user_subp_a.set_defaults(func=delete_user)

    # Reset application state
    reset_subp = subps.add_parser('reset', help='DANGER!!! Clears the '
                                  "SecureDrop application's state.")
    reset_subp.set_defaults(func=reset)
    # Cleanup the SD temp dir
    set_clean_tmp_parser(subps, 'clean-tmp')
    set_clean_tmp_parser(subps, 'clean_tmp')

    set_translate_parser(subps)

    return parser


def set_translate_parser(subps):
    parser = subps.add_parser('translate',
                              help='Update and compile translations')
    translations_dir = 'translations'
    parser.add_argument(
        '--extract-update',
        action='store_true',
        help='run pybabel extract and pybabel update')
    parser.add_argument(
        '--compile',
        action='store_true',
        help='run pybabel compile')
    mapping = 'babel.cfg'
    parser.add_argument(
        '--mapping',
        default=mapping,
        help='Mapping of files to consider (default {})'.format(
            mapping))
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
    sources = ['.', 'source_templates', 'journalist_templates']
    parser.add_argument(
        '--source',
        default=sources,
        action='append',
        help='Source file or directory to extract (default {})'.format(
            sources))
    parser.set_defaults(func=translate)


def set_clean_tmp_parser(subps, name):
    parser = subps.add_parser(name, help='Cleanup the '
                              'SecureDrop temp directory.')
    default_days = 7
    parser.add_argument(
        '--days',
        default=default_days,
        type=int,
        help=('remove files not modified in a given number of DAYS '
              '(default {} days)'.format(default_days)))
    parser.add_argument(
        '--directory',
        default=config.TEMP_DIR,
        help=('remove old files from DIRECTORY '
              '(default {})'.format(config.TEMP_DIR)))
    parser.set_defaults(func=clean_tmp)


def setup_gnupg_verbosity():
    gnupg_logger = logging.getLogger('gnupg')
    gnupg_logger.setLevel(logging.ERROR)
    valid_levels = {'INFO': logging.INFO, 'DEBUG': logging.DEBUG}
    gnupg_level = valid_levels.get(os.environ.get('GNUPG_LOG_LEVEL', None), None)
    if gnupg_level:
        gnupg_logger.setLevel(gnupg_level)

def setup_verbosity(args):
    if args.verbose:
        logging.getLogger(__name__).setLevel(logging.DEBUG)
    else:
        logging.getLogger(__name__).setLevel(logging.INFO)


# run on startup to squelch early on
setup_gnupg_verbosity()


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
