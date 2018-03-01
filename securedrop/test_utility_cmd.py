#/usr/bin/env python
import os
import sys
import argparse

from sqlalchemy.orm.exc import NoResultFound

os.environ['SECUREDROP_ENV'] = 'dev'  # noqa
import config
import crypto_util
from models import (db_session, init_db, Journalist, PasswordError,
                InvalidUsernameException)
from management.run import run

def _make_password():
    while True:
        password = crypto_util.genrandomid(7)
        try:
            Journalist.check_password_acceptable(password)
            return password
        except PasswordError:
            continue


def add_user(username, is_admin):
    password = _make_password()
    print("This user's password is: {}".format(password))

    otp_secret = None
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
    uri = user.totp.provisioning_uri(username,
                                         issuer_name='SecureDrop')
    print("secret: {}".format(user.formatted_otp_secret))

if __name__ == '__main__':
    ret_code = 0
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", help="username")
    parser.add_argument("--admin", help="Is this an admin?", action="store_true")
    args = parser.parse_args()
    if args.username:
	ret_code =add_user(args.username, args.admin)

    sys.exit(ret_code)

