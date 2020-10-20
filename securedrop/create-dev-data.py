#!/opt/venvs/securedrop-app-code/bin/python
# -*- coding: utf-8 -*-

import datetime
import io
import os
import argparse
import math
from itertools import cycle

from flask import current_app
from sqlalchemy.exc import IntegrityError

os.environ["SECUREDROP_ENV"] = "dev"  # noqa
import journalist_app

from sdconfig import config
from db import db
from models import Journalist, Reply, SeenFile, SeenMessage, SeenReply, Source, Submission
from specialstrings import strings


messages = cycle(strings)
replies = cycle(strings)


def main(staging=False):
    app = journalist_app.create_app(config)
    with app.app_context():
        # Add two test users
        test_password = "correct horse battery staple profanity oil chewy"
        test_otp_secret = "JHCOGO7VCER3EJ4L"

        journalist_who_saw = add_test_user(
            "journalist",
            test_password,
            test_otp_secret,
            is_admin=True
        )

        if staging:
            return

        dellsberg = add_test_user(
            "dellsberg",
            test_password,
            test_otp_secret,
            is_admin=False
        )

        journalist_tobe_deleted = add_test_user("clarkkent",
                                                test_password,
                                                test_otp_secret,
                                                is_admin=False,
                                                first_name="Clark",
                                                last_name="Kent")

        NUM_SOURCES = os.getenv('NUM_SOURCES', 3)
        if NUM_SOURCES == "ALL":
            # We ingest two strings per source, so this will create the required
            # number of sources to include all special strings
            NUM_SOURCES = math.ceil(len(strings) / 2)

        # Create source data
        num_sources = int(NUM_SOURCES)
        for i in range(num_sources):
            # For the first source, the journalist who replied will be deleted, otherwise dellsberg
            journalist_who_replied = journalist_tobe_deleted if i == 0 else dellsberg

            create_source_data(
                i,
                num_sources,
                journalist_who_replied,
                journalist_who_saw
            )

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


def create_source_data(
    source_index,
    source_count,
    journalist_who_replied,
    journalist_who_saw,
    num_files=2,
    num_messages=2,
    num_replies=2,
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

    # Mark a third of sources as seen, a third as partially-seen, and a third as unseen
    seen_files = 0 if source_index % 3 == 0 else math.floor(num_files / (source_index % 3))
    seen_messages = 0 if source_index % 3 == 0 else math.floor(num_messages / (source_index % 3))
    seen_replies = 0 if source_index % 3 == 0 else math.floor(num_replies / (source_index % 3))

    # Generate some test messages
    seen_messages_count = 0
    for _ in range(num_messages):
        source.interaction_count += 1
        submission_text = next(messages)
        fpath = current_app.storage.save_message_submission(
            source.filesystem_id,
            source.interaction_count,
            source.journalist_filename,
            submission_text
        )
        source.last_updated = datetime.datetime.utcnow()
        submission = Submission(source, fpath)
        db.session.add(submission)
        if seen_messages_count < seen_messages:
            seen_messages_count = seen_messages_count + 1
            db.session.flush()
            seen_message = SeenMessage(
                message_id=submission.id,
                journalist_id=journalist_who_saw.id
            )
            db.session.add(seen_message)

    # Generate some test files
    seen_files_count = 0
    for _ in range(num_files):
        source.interaction_count += 1
        fpath = current_app.storage.save_file_submission(
            source.filesystem_id,
            source.interaction_count,
            source.journalist_filename,
            "memo.txt",
            io.BytesIO(b"This is an example of a plain text file upload.")
        )
        source.last_updated = datetime.datetime.utcnow()
        submission = Submission(source, fpath)
        db.session.add(submission)
        if seen_files_count < seen_files:
            seen_files_count = seen_files_count + 1
            db.session.flush()
            seen_file = SeenFile(
                file_id=submission.id,
                journalist_id=journalist_who_saw.id
            )
            db.session.add(seen_file)

    # Generate some test replies
    seen_replies_count = 0
    for _ in range(num_replies):
        source.interaction_count += 1
        fname = "{}-{}-reply.gpg".format(source.interaction_count,
                                         source.journalist_filename)
        current_app.crypto_util.encrypt(
            next(replies),
            [current_app.crypto_util.get_fingerprint(source.filesystem_id),
             config.JOURNALIST_KEY],
            current_app.storage.path(source.filesystem_id, fname))

        reply = Reply(journalist_who_replied, source, fname)
        db.session.add(reply)
        db.session.flush()
        # Journalist who replied has seen the reply
        seen_reply = SeenReply(
            reply_id=reply.id,
            journalist_id=journalist_who_replied.id
        )
        db.session.add(seen_reply)
        if seen_replies_count < seen_replies:
            seen_replies_count = seen_replies_count + 1
            seen_reply = SeenReply(
                reply_id=reply.id,
                journalist_id=journalist_who_saw.id
            )
            db.session.add(seen_reply)

    db.session.commit()

    print(
        "Test source {}/{} (codename: '{}', journalist designation '{}') "
        "added with {} files, {} messages, and {} replies".format(
            source_index + 1,
            source_count,
            codename,
            journalist_designation,
            num_files,
            num_messages,
            num_replies
        )
    )


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("--staging", help="Adding user for staging tests.",
                        action="store_true")
    args = parser.parse_args()

    main(args.staging)
