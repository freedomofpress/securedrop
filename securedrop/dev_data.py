#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from sqlalchemy.exc import IntegrityError

os.environ["SECUREDROP_ENV"] = "dev"  # noqa
import journalist_app
import config
from db import db
from models import Journalist


def add_test_user(username, password, otp_secret, is_admin=False):
    context = journalist_app.create_app(config).app_context()
    context.push()

    try:
        user = Journalist(username=username,
                          password=password,
                          is_admin=is_admin,
                          is_totp=True)
        user.otp_secret = otp_secret
        db.session.add(user)
        db.session.commit()
        print("""Test user successfully added:
                 username={}, password={}, otp_secret={}
              """.format(username, password, otp_secret))
    except IntegrityError:
        print("Test user already added")
        db.session.rollback()

    context.pop()


if __name__ == "__main__":  # pragma: no cover
    add_test_user("journalist",
                  "correct horse battery staple profanity oil chewy",
                  "JHCOGO7VCER3EJ4L")
