#!/opt/venvs/securedrop-app-code/bin/python
# -*- coding: utf-8 -*-

import datetime
import os
import argparse
from itertools import cycle

from flask import current_app
from sqlalchemy.exc import IntegrityError

os.environ["SECUREDROP_ENV"] = "dev"  # noqa
import journalist_app

from sdconfig import config
from db import db
from models import Journalist, Reply, Source, Submission

submissions = cycle([
    'This is a test submission without markup!',
    'This is a test submission with markup and characters such as \, \\, \', \" and ". ' +  # noqa: W605, E501
    '<strong>This text should not be bold</strong>!'
])

replies = cycle([
    'This is a test reply without markup!',
    'This is a test reply with markup and characters such as \, \\, \', \" and ". ' +  # noqa: W605, E501
    '<strong>This text should not be bold</strong>!'
])


def main(staging=False):
    app = journalist_app.create_app(config)
    with app.app_context():
        # Add two test users
        test_password = "correct horse battery staple profanity oil chewy"
        test_otp_secret = "JHCOGO7VCER3EJ4L"

        add_test_user("journalist",
                      test_password,
                      test_otp_secret,
                      is_admin=True)

        if staging:
            return

        add_test_user("dellsberg",
                      test_password,
                      test_otp_secret,
                      is_admin=False)

        journalist_tobe_deleted = add_test_user("clarkkent",
                                                test_password,
                                                test_otp_secret,
                                                is_admin=False,
                                                first_name="Clark",
                                                last_name="Kent")

        # Add test sources and submissions
        num_sources = int(os.getenv('NUM_SOURCES', 2))
        for i in range(1, num_sources + 1):
            if i == 1:
                # For the first source, the journalist who replied will be deleted
                create_source_and_submissions(
                    i, num_sources, journalist_who_replied=journalist_tobe_deleted
                )
                continue
            create_source_and_submissions(i, num_sources)
        # Now let us delete one journalist
        db.session.delete(journalist_tobe_deleted)
        db.session.commit()


def add_test_user(username, password, otp_secret, is_admin=False,
                  first_name="", last_name=""):
    try:
        user = Journalist(username=username,
                          password=password,
                          is_admin=is_admin,
                          first_name=first_name,
                          last_name=last_name)
        user.otp_secret = otp_secret
        db.session.add(user)
        db.session.commit()
        print('Test user successfully added: '
              'username={}, password={}, otp_secret={}, is_admin={}'
              ''.format(username, password, otp_secret, is_admin))
        return user
    except IntegrityError:
        print("Test user already added")
        db.session.rollback()


def create_source_and_submissions(
    source_index, source_count, num_submissions=2, num_replies=2, journalist_who_replied=None
):
    # Store source in database
    codename = current_app.crypto_util.genrandomid()
    filesystem_id = current_app.crypto_util.hash_codename(codename)
    journalist_designation = current_app.crypto_util.display_id()
    source = Source(filesystem_id, journalist_designation)
    source.pending = False
    db.session.add(source)
    db.session.commit()

    # Generate submissions directory and generate source key
    os.mkdir(current_app.storage.path(source.filesystem_id))
    current_app.crypto_util.genkeypair(source.filesystem_id, codename)

    # Generate some test submissions
    for _ in range(num_submissions):
        source.interaction_count += 1
        fpath = current_app.storage.save_message_submission(
            source.filesystem_id,
            source.interaction_count,
            source.journalist_filename,
            next(submissions)
        )
        source.last_updated = datetime.datetime.utcnow()
        submission = Submission(source, fpath)
        db.session.add(submission)

    # Generate some test replies
    for _ in range(num_replies):
        source.interaction_count += 1
        fname = "{}-{}-reply.gpg".format(source.interaction_count,
                                         source.journalist_filename)
        current_app.crypto_util.encrypt(
            next(replies),
            [current_app.crypto_util.get_fingerprint(source.filesystem_id),
             config.JOURNALIST_KEY],
            current_app.storage.path(source.filesystem_id, fname))

        if not journalist_who_replied:
            journalist = Journalist.query.first()
        else:
            journalist = journalist_who_replied
        reply = Reply(journalist, source, fname)
        db.session.add(reply)

    db.session.commit()

    print(
        "Test source {}/{} (codename: '{}', journalist designation '{}') "
        "added with {} submissions and {} replies".format(
            source_index, source_count, codename, journalist_designation,
            num_submissions, num_replies
        )
    )


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("--staging", help="Adding user for staging tests.",
                        action="store_true")
    args = parser.parse_args()

    main(args.staging)
