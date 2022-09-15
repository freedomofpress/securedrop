#!/opt/venvs/securedrop-app-code/bin/python
# -*- coding: utf-8 -*-

import argparse
import logging
import os
import pwd
import shutil
import signal
import subprocess
import sys
import time
import traceback
from argparse import _SubParsersAction
from typing import List, Optional

from flask.ctx import AppContext
from passphrases import PassphraseGenerator

sys.path.insert(0, "/var/www/securedrop")  # noqa: E402

import qrcode  # noqa: E402
from sqlalchemy.orm.exc import NoResultFound  # noqa: E402

if not os.environ.get("SECUREDROP_ENV"):
    os.environ["SECUREDROP_ENV"] = "dev"  # noqa


from db import db  # noqa: E402
from management import app_context, config  # noqa: E402
from management.run import run  # noqa: E402
from management.submissions import (  # noqa: E402
    add_check_db_disconnect_parser,
    add_check_fs_disconnect_parser,
    add_delete_db_disconnect_parser,
    add_delete_fs_disconnect_parser,
    add_list_db_disconnect_parser,
    add_list_fs_disconnect_parser,
    add_were_there_submissions_today,
)
from models import FirstOrLastNameError, InvalidUsernameException, Journalist  # noqa: E402

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def obtain_input(text: str) -> str:
    """Wrapper for testability as suggested in
    https://github.com/pytest-dev/pytest/issues/1598#issuecomment-224761877"""
    return input(text)


def reset(args: argparse.Namespace, context: Optional[AppContext] = None) -> int:
    """Clears the SecureDrop development applications' state, restoring them to
    the way they were immediately after running `setup_dev.sh`. This command:
    1. Erases the development sqlite database file.
    2. Regenerates the database.
    3. Erases stored submissions and replies from the store dir.
    """
    # Erase the development db file
    if not hasattr(config, "DATABASE_FILE"):
        raise Exception(
            "./manage.py doesn't know how to clear the db " "if the backend is not sqlite"
        )

    # we need to save some data about the old DB file so we can recreate it
    # with the same state
    try:
        stat_res = os.stat(config.DATABASE_FILE)
        uid = stat_res.st_uid
        gid = stat_res.st_gid
    except OSError:
        uid = os.getuid()
        gid = os.getgid()

    try:
        os.remove(config.DATABASE_FILE)
    except OSError:
        pass

    # Regenerate the database
    # 1. Create it
    subprocess.check_call(["sqlite3", config.DATABASE_FILE, ".databases"])
    # 2. Set permissions on it
    os.chown(config.DATABASE_FILE, uid, gid)
    os.chmod(config.DATABASE_FILE, 0o0640)

    if os.environ.get("SECUREDROP_ENV") == "dev":
        # 3. Create the DB from the metadata directly when in 'dev' so
        # developers can test application changes without first writing
        # alembic migration.
        with context or app_context():
            db.create_all()
    else:
        # We have to override the hardcoded .ini file because during testing
        # the value in the .ini doesn't exist.
        ini_dir = os.path.dirname(getattr(config, "TEST_ALEMBIC_INI", "alembic.ini"))

        # 3. Migrate it to 'head'
        # nosemgrep: python.lang.security.audit.subprocess-shell-true.subprocess-shell-true
        subprocess.check_call("cd {} && alembic upgrade head".format(ini_dir), shell=True)  # nosec

    # Clear submission/reply storage
    try:
        os.stat(args.store_dir)
    except OSError:
        pass
    else:
        for source_dir in os.listdir(args.store_dir):
            try:
                # Each entry in STORE_DIR is a directory corresponding
                # to a source
                shutil.rmtree(os.path.join(args.store_dir, source_dir))
            except OSError:
                pass
    return 0


def add_admin(args: argparse.Namespace) -> int:
    return _add_user(is_admin=True)


def add_journalist(args: argparse.Namespace) -> int:
    return _add_user()


def _get_username() -> str:
    while True:
        username = obtain_input("Username: ")
        try:
            Journalist.check_username_acceptable(username)
        except InvalidUsernameException as e:
            print("Invalid username: " + str(e))
        else:
            return username


def _get_first_name() -> Optional[str]:
    while True:
        first_name = obtain_input("First name: ")
        if not first_name:
            return None
        try:
            Journalist.check_name_acceptable(first_name)
            return first_name
        except FirstOrLastNameError as e:
            print("Invalid name: " + str(e))


def _get_last_name() -> Optional[str]:
    while True:
        last_name = obtain_input("Last name: ")
        if not last_name:
            return None
        try:
            Journalist.check_name_acceptable(last_name)
            return last_name
        except FirstOrLastNameError as e:
            print("Invalid name: " + str(e))


def _get_yubikey_usage() -> bool:
    """Function used to allow for test suite mocking"""
    while True:
        answer = (
            obtain_input("Will this user be using a YubiKey [HOTP]? " "(y/N): ").lower().strip()
        )
        if answer in ("y", "yes"):
            return True
        elif answer in ("", "n", "no"):
            return False
        else:
            print('Invalid answer. Please type "y" or "n"')


def _add_user(is_admin: bool = False, context: Optional[AppContext] = None) -> int:
    with context or app_context():
        username = _get_username()
        first_name = _get_first_name()
        last_name = _get_last_name()

        print("Note: Passwords are now autogenerated.")
        password = PassphraseGenerator.get_default().generate_passphrase()
        print("This user's password is: {}".format(password))

        is_hotp = _get_yubikey_usage()
        otp_secret = None
        if is_hotp:
            while True:
                otp_secret = obtain_input(
                    "Please configure this user's YubiKey and enter the " "secret: "
                )
                if otp_secret:
                    tmp_str = otp_secret.replace(" ", "")
                    if len(tmp_str) != 40:
                        print(
                            "The length of the secret is not correct. "
                            "Expected 40 characters, but received {0}. "
                            "Try again.".format(len(tmp_str))
                        )
                        continue
                if otp_secret:
                    break

        try:
            user = Journalist(
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password,
                is_admin=is_admin,
                otp_secret=otp_secret,
            )
            db.session.add(user)
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            if "UNIQUE constraint failed: journalists.username" in str(exc):
                print("ERROR: That username is already taken!")
            else:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            return 1
        else:
            print('User "{}" successfully added'.format(username))
            if not otp_secret:
                # Print the QR code for FreeOTP
                print("\nScan the QR code below with FreeOTP:\n")
                uri = user.totp.provisioning_uri(username, issuer_name="SecureDrop")
                qr = qrcode.QRCode()
                qr.add_data(uri)
                qr.print_ascii(tty=sys.stdout.isatty())
                print(
                    "\nIf the barcode does not render correctly, try "
                    "changing your terminal's font (Monospace for Linux, "
                    "Menlo for OS X). If you are using iTerm on Mac OS X, "
                    'you will need to change the "Non-ASCII Font", which '
                    "is your profile's Text settings.\n\nCan't scan the "
                    "barcode? Enter following shared secret manually:"
                    "\n{}\n".format(user.formatted_otp_secret)
                )
        return 0


def _get_username_to_delete() -> str:
    return obtain_input("Username to delete: ")


def _get_delete_confirmation(username: str) -> bool:
    confirmation = obtain_input(
        "Are you sure you want to delete user " '"{}" (y/n)?'.format(username)
    )
    if confirmation.lower() != "y":
        print('Confirmation not received: user "{}" was NOT ' "deleted".format(username))
        return False
    return True


def delete_user(args: argparse.Namespace, context: Optional[AppContext] = None) -> int:
    """Deletes a journalist or admin from the application."""
    with context or app_context():
        username = _get_username_to_delete()
        try:
            selected_user = Journalist.query.filter_by(username=username).one()
        except NoResultFound:
            print("ERROR: That user was not found!")
            return 0

        # Confirm deletion if user is found
        if not _get_delete_confirmation(selected_user.username):
            return 0

        # Try to delete user from the database
        try:
            db.session.delete(selected_user)
            db.session.commit()
        except Exception as e:
            # If the user was deleted between the user selection and
            # confirmation, (e.g., through the web app), we don't report any
            # errors. If the user is still there, but there was a error
            # deleting them from the database, we do report it.
            try:
                Journalist.query.filter_by(username=username).one()
            except NoResultFound:
                pass
            else:
                raise e

        print('User "{}" successfully deleted'.format(username))
    return 0


def clean_tmp(args: argparse.Namespace) -> int:
    """Cleanup the SecureDrop temp directory."""
    if not os.path.exists(args.directory):
        log.debug("{} does not exist, do nothing".format(args.directory))
        return 0

    def listdir_fullpath(d: str) -> List[str]:
        return [os.path.join(d, f) for f in os.listdir(d)]

    too_old = args.days * 24 * 60 * 60
    for path in listdir_fullpath(args.directory):
        if time.time() - os.stat(path).st_mtime > too_old:
            os.remove(path)
            log.debug("{} removed".format(path))
        else:
            log.debug("{} modified less than {} days ago".format(path, args.days))

    return 0


def init_db(args: argparse.Namespace) -> None:
    user = pwd.getpwnam(args.user)
    subprocess.check_call(["sqlite3", config.DATABASE_FILE, ".databases"])
    os.chown(config.DATABASE_FILE, user.pw_uid, user.pw_gid)
    os.chmod(config.DATABASE_FILE, 0o0640)
    subprocess.check_call(["alembic", "upgrade", "head"])


def get_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=__file__, description="Management " "and testing utility for SecureDrop."
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "--data-root",
        default=config.SECUREDROP_DATA_ROOT,
        help=("directory in which the securedrop " "data is stored"),
    )
    parser.add_argument(
        "--store-dir",
        default=config.STORE_DIR,
        help=("directory in which the files are stored"),
    )
    subps = parser.add_subparsers()
    # Add/remove journalists + admins
    admin_subp = subps.add_parser("add-admin", help="Add an admin to the " "application.")
    admin_subp.set_defaults(func=add_admin)
    admin_subp_a = subps.add_parser("add_admin", help="^")
    admin_subp_a.set_defaults(func=add_admin)
    journalist_subp = subps.add_parser(
        "add-journalist", help="Add a " "journalist to the application."
    )
    journalist_subp.set_defaults(func=add_journalist)
    journalist_subp_a = subps.add_parser("add_journalist", help="^")
    journalist_subp_a.set_defaults(func=add_journalist)
    delete_user_subp = subps.add_parser(
        "delete-user", help="Delete a user " "from the application."
    )
    delete_user_subp.set_defaults(func=delete_user)
    delete_user_subp_a = subps.add_parser("delete_user", help="^")
    delete_user_subp_a.set_defaults(func=delete_user)

    add_check_db_disconnect_parser(subps)
    add_check_fs_disconnect_parser(subps)
    add_delete_db_disconnect_parser(subps)
    add_delete_fs_disconnect_parser(subps)
    add_list_db_disconnect_parser(subps)
    add_list_fs_disconnect_parser(subps)

    # Cleanup the SD temp dir
    set_clean_tmp_parser(subps, "clean-tmp")
    set_clean_tmp_parser(subps, "clean_tmp")

    init_db_subp = subps.add_parser("init-db", help="Initialize the database.\n")
    init_db_subp.add_argument("-u", "--user", help="Unix user for the DB", required=True)
    init_db_subp.set_defaults(func=init_db)

    add_were_there_submissions_today(subps)

    # Run WSGI app
    run_subp = subps.add_parser(
        "run",
        help="DANGER!!! ONLY FOR DEVELOPMENT "
        "USE. DO NOT USE IN PRODUCTION. Run the "
        "Werkzeug source and journalist WSGI apps.\n",
    )
    run_subp.set_defaults(func=run)

    # Reset application state
    reset_subp = subps.add_parser(
        "reset",
        help="DANGER!!! ONLY FOR DEVELOPMENT "
        "USE. DO NOT USE IN PRODUCTION. Clear the "
        "SecureDrop application's state.\n",
    )
    reset_subp.set_defaults(func=reset)
    return parser


def set_clean_tmp_parser(subps: _SubParsersAction, name: str) -> None:
    parser = subps.add_parser(name, help="Cleanup the " "SecureDrop temp directory.")
    default_days = 7
    parser.add_argument(
        "--days",
        default=default_days,
        type=int,
        help=(
            "remove files not modified in a given number of DAYS "
            "(default {} days)".format(default_days)
        ),
    )
    parser.add_argument(
        "--directory",
        default=config.TEMP_DIR,
        help=("remove old files from DIRECTORY " "(default {})".format(config.TEMP_DIR)),
    )
    parser.set_defaults(func=clean_tmp)


def setup_verbosity(args: argparse.Namespace) -> None:
    if args.verbose:
        logging.getLogger(__name__).setLevel(logging.DEBUG)
    else:
        logging.getLogger(__name__).setLevel(logging.INFO)


def _run_from_commandline() -> None:  # pragma: no cover
    try:
        parser = get_args()
        args = parser.parse_args()
        setup_verbosity(args)
        try:
            rc = args.func(args)
            sys.exit(rc)
        except AttributeError:
            parser.print_help()
            parser.exit()
    except KeyboardInterrupt:
        sys.exit(signal.SIGINT)


if __name__ == "__main__":  # pragma: no cover
    _run_from_commandline()
