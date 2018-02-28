#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from sqlalchemy.exc import IntegrityError

os.environ["SECUREDROP_ENV"] = "dev"  # noqa
import journalist_app
from sdconfig import config
from db import db
from models import Journalist


def add_test_user(username, password, otp_secret, is_admin=False):
    context = journalist_app.create_app(config).app_context()
    context.push()
    valid_password = "correct horse battery staple profanity oil chewy"

    try:
        user = Journalist(username=username,
                          password=valid_password,
                          is_admin=is_admin)
        user.otp_secret = otp_secret
        user.pw_salt = user._gen_salt()
        user.pw_hash = user._scrypt_hash(password, user.pw_salt)
        db.session.add(user)
        db.session.commit()
        print('Test user successfully added: '
              'username={}, password={}, otp_secret={}'
              ''.format(username, password, otp_secret))
    except IntegrityError:
        print("Test user already added")
        db.session.rollback()

    context.pop()


if __name__ == "__main__":  # pragma: no cover
    add_test_user("journalist",
                  "WEjwn8ZyczDhQSK24YKM8C9a",
                  "JHCOGO7VCER3EJ4L",
                  is_admin=True)
