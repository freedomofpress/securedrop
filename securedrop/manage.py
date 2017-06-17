#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from getpass import getpass
import logging
import os
import shutil
import signal
import sys
import traceback

import qrcode
from sqlalchemy.orm.exc import NoResultFound

os.environ['SECUREDROP_ENV'] = 'dev'  # noqa
import config
from db import db_session, init_db, Journalist
from management.run import run

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)


def reset(args):  # pragma: no cover
    """Clears the SecureDrop development applications' state, restoring them to
    the way they were immediately after running `setup_dev.sh`. This command:
    1. Erases the development sqlite database file.
    2. Regenerates the database.
    3. Erases stored submissions and replies from the store dir.
    """
    # Erase the development db file
    assert hasattr(config, 'DATABASE_FILE'), ("TODO: ./manage.py doesn't know "
                                              'how to clear the db if the '
                                              'backend is not sqlite')
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


def add_admin(args):  # pragma: no cover
    return _add_user(is_admin=True)


def add_journalist(args):  # pragma: no cover
    return _add_user()


def _add_user(is_admin=False):  # pragma: no cover
    while True:
        username = raw_input('Username: ')
        password = getpass('Password: ')
        password_again = getpass('Confirm Password: ')

        if len(password) > Journalist.MAX_PASSWORD_LEN:
            print('Your password is too long (maximum length {} characters). '
                  'Please pick a shorter '
                  'password.'.format(Journalist.MAX_PASSWORD_LEN))
            continue

        if len(password) < Journalist.MIN_PASSWORD_LEN:
            print('Error: Password needs to be at least {} characters.'.format(
                Journalist.MIN_PASSWORD_LEN
            ))
            continue

        if password == password_again:
            break
        print("Passwords didn't match!")

    hotp_input = raw_input('Will this user be using a YubiKey [HOTP]? (y/N): ')
    otp_secret = None
    if hotp_input.lower() in ('y', 'yes'):
        while True:
            otp_secret = raw_input(
                'Please configure your YubiKey and enter the secret: ')
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
            qr.print_ascii(tty=sys.stdout.isatty())
            print('\nIf the barcode does not render correctly, try changing '
                  "your terminal's font (Monospace for Linux, Menlo for OS "
                  'X). If you are using iTerm on Mac OS X, you will need to '
                  'change the "Non-ASCII Font", which is your profile\'s Text '
                  "settings.\n\nCan't scan the barcode? Enter following "
                  'shared secret '
                  'manually:\n{}\n'.format(user.formatted_otp_secret))
        return 0


def delete_user(args):  # pragma: no cover
    """Deletes a journalist or administrator from the application."""
    # Select user to delete
    username = raw_input('Username to delete: ')
    try:
        selected_user = Journalist.query.filter_by(username=username).one()
    except NoResultFound:
        print('ERROR: That user was not found!')
        return 0

    # Confirm deletion if user is found
    confirmation = raw_input('Are you sure you want to delete user '
                             '{} (y/n)?'.format(selected_user))
    if confirmation.lower() != 'y':
        print('Confirmation not received: user "{}" was NOT '
              'deleted'.format(username))
        return 0

    # Try to delete user from the database
    try:
        db_session.delete(selected_user)
        db_session.commit()
    except:
        # If the user was deleted between the user selection and confirmation,
        # (e.g., through the web app), we don't report any errors. If the user
        # is still there, but there was a error deleting them from the
        # database, we do report it.
        try:
            selected_user = Journalist.query.filter_by(username=username).one()
        except NoResultFound:
            pass
        else:
            raise

    print('User "{}" successfully deleted'.format(username))
    return 0


def clean_tmp(args):
    """Cleanup the SecureDrop temp directory. """
    try:
        os.stat(config.TEMP_DIR)
    except OSError:
        pass
    else:
        for path in listdir_fullpath(config.TEMP_DIR):
            if not file_in_use(path):
                os.remove(path)

    return 0


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
    clean_tmp_subp = subps.add_parser('clean-tmp', help='Cleanup the '
                                      'SecureDrop temp directory.')
    clean_tmp_subp.set_defaults(func=clean_tmp)
    clean_tmp_subp_a = subps.add_parser('clean_tmp', help='^')
    clean_tmp_subp_a.set_defaults(func=clean_tmp)

    return parser


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
