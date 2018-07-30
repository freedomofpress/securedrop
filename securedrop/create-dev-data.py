#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from sqlalchemy.exc import IntegrityError

os.environ["SECUREDROP_ENV"] = "dev"  # noqa
import journalist_app
from sdconfig import config
from db import db
from models import Journalist, Source, Submission


def add_test_user(username, password, otp_secret, is_admin=False):
    context = journalist_app.create_app(config).app_context()
    context.push()

    try:
        user = Journalist(username=username,
                          password=password,
                          is_admin=is_admin)
        user.otp_secret = otp_secret
        db.session.add(user)
        db.session.commit()
        print('Test user successfully added: '
              'username={}, password={}, otp_secret={}, is_admin={}'
              ''.format(username, password, otp_secret, is_admin))
    except IntegrityError:
        print("Test user already added")
        db.session.rollback()

    context.pop()


def create_source_and_submissions(num_submissions=2):
    app = journalist_app.create_app(config)

    with app.app_context():
        # Store source in database
        codename = app.crypto_util.genrandomid()
        filesystem_id = app.crypto_util.hash_codename(codename)
        journalist_designation = app.crypto_util.display_id()
        source = Source(filesystem_id, journalist_designation)
        source.pending = False
        db.session.add(source)
        db.session.commit()

        # Generate submissions directory and generate source key
        os.mkdir(app.storage.path(source.filesystem_id))
        app.crypto_util.genkeypair(source.filesystem_id, codename)

        # Generate some test submissions
        for _ in range(num_submissions):
            source.interaction_count += 1
            fpath = app.storage.save_message_submission(
                source.filesystem_id,
                source.interaction_count,
                source.journalist_filename,
                'test submission!'
            )
            submission = Submission(source, fpath)
            db.session.add(submission)

        db.session.commit()
        print("Test source '{}' added with {} submissions".format(
            journalist_designation, num_submissions)
        )


if __name__ == "__main__":  # pragma: no cover
    # Add two test users
    test_password = "correct horse battery staple profanity oil chewy"
    test_otp_secret = "JHCOGO7VCER3EJ4L"

    add_test_user("journalist",
                  test_password,
                  test_otp_secret,
                  is_admin=True)
    add_test_user("dellsberg",
                  test_password,
                  test_otp_secret,
                  is_admin=False)

    # Add test sources and submissions
    num_sources = 2
    for _ in range(num_sources):
        create_source_and_submissions()
