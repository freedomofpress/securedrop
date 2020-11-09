#!/opt/venvs/securedrop-app-code/bin/python
# -*- coding: utf-8 -*-

import argparse
import datetime
import io
import math
import os
import random
import string
from itertools import cycle
from typing import Optional, Tuple

from flask import current_app
from sqlalchemy.exc import IntegrityError

import journalist_app
from db import db
from models import (
    Journalist,
    JournalistLoginAttempt,
    Reply,
    SeenFile,
    SeenMessage,
    SeenReply,
    Source,
    SourceStar,
    Submission,
)
from passphrases import PassphraseGenerator
from sdconfig import config
from specialstrings import strings

messages = cycle(strings)
replies = cycle(strings)


def fraction(s: str) -> float:
    """
    Ensures the string is a float between 0 and 1.
    """
    f = float(s)
    if 0 <= f <= 1:
        return f
    raise ValueError("{} should be a float between 0 and 1".format(s))


def non_negative_int(s: str) -> int:
    """
    Ensures the string is a non-negative integer.
    """
    f = float(s)
    if f.is_integer() and f >= 0:
        return int(f)
    raise ValueError("{} is not a non-negative integer".format(s))


def random_bool() -> bool:
    """
    Flips a coin.
    """
    return random.choice((True, False))


def random_chars(count: int, chars: str = string.ascii_letters) -> str:
    """
    Returns a random string of len characters from the supplied list.
    """
    return "".join([random.choice(chars) for _ in range(count)])


def random_datetime(nullable: bool) -> Optional[datetime.datetime]:
    """
    Returns a random datetime or possibly None if nullable.
    """
    if nullable and random_bool():
        return None

    now = datetime.datetime.now()
    return datetime.datetime(
        year=random.randint(2013, now.year),
        month=random.randint(1, now.month),
        day=random.randint(1, now.day),
        hour=random.randint(0, 23),
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
        microsecond=random.randint(0, 1000),
    )


def default_journalist_count() -> str:
    return os.environ.get("NUM_JOURNALISTS", "0")


def default_source_count() -> str:
    return os.environ.get("NUM_SOURCES", "3")


def set_source_count(s: str) -> int:
    """
    Sets the source count from command line arguments.

    The --source-count argument can be either a positive integer or
    the special string "ALL", which will result in a number of sources
    that can demonstrate all of the special strings we want to test,
    if each source uses two of the strings.
    """
    if s == "ALL":
        return math.ceil(len(strings) / 2)
    return non_negative_int(s)


def add_journalist(
    username: str = "",
    is_admin: bool = False,
    first_name: str = "",
    last_name: str = "",
) -> Journalist:
    """
    Adds a single journalist account.
    """
    test_password = "correct horse battery staple profanity oil chewy"
    test_otp_secret = "JHCOGO7VCER3EJ4L"

    if not username:
        username = current_app.crypto_util.display_id()

    journalist = Journalist(
        username=username,
        password=test_password,
        first_name=first_name,
        last_name=last_name,
        is_admin=is_admin,
    )
    journalist.otp_secret = test_otp_secret
    if random_bool():
        # to add legacy passwords back in
        journalist.passphrase_hash = None
        salt = random_chars(32).encode("utf-8")
        journalist.pw_salt = salt
        journalist.pw_hash = journalist._scrypt_hash(test_password, salt)

    db.session.add(journalist)
    attempt = JournalistLoginAttempt(journalist)
    attempt.timestamp = random_datetime(nullable=True)
    db.session.add(attempt)
    db.session.commit()
    print(
        "Journalist successfully added: "
        "username={}, password={}, otp_secret={}, is_admin={}"
        "".format(username, test_password, test_otp_secret, is_admin)
    )
    return journalist


def record_source_interaction(source) -> None:
    """
    Updates the source's interaction count, pending status, and timestamp.
    """
    source.interaction_count += 1
    source.pending = False
    source.last_updated = datetime.datetime.utcnow()
    db.session.flush()


def submit_message(source: Source, journalist_who_saw: Optional[Journalist]) -> None:
    """
    Adds a single message submitted by a source.
    """
    record_source_interaction(source)
    fpath = current_app.storage.save_message_submission(
        source.filesystem_id,
        source.interaction_count,
        source.journalist_filename,
        next(messages),
    )
    submission = Submission(source, fpath)
    db.session.add(submission)
    db.session.flush()

    if journalist_who_saw:
        seen_message = SeenMessage(
            message_id=submission.id, journalist_id=journalist_who_saw.id
        )
        db.session.add(seen_message)
        db.session.flush()


def submit_file(source: Source, journalist_who_saw: Optional[Journalist]) -> None:
    """
    Adds a single file submitted by a source.
    """
    record_source_interaction(source)
    fpath = current_app.storage.save_file_submission(
        source.filesystem_id,
        source.interaction_count,
        source.journalist_filename,
        "memo.txt",
        io.BytesIO(b"This is an example of a plain text file upload."),
    )
    submission = Submission(source, fpath)
    db.session.add(submission)
    db.session.flush()

    if journalist_who_saw:
        seen_file = SeenFile(file_id=submission.id, journalist_id=journalist_who_saw.id)
        db.session.add(seen_file)
        db.session.flush()


def add_reply(
    source: Source, journalist: Journalist, journalist_who_saw: Optional[Journalist]
) -> None:
    """
    Adds a single reply to a source.
    """
    record_source_interaction(source)
    fname = "{}-{}-reply.gpg".format(
        source.interaction_count, source.journalist_filename
    )
    current_app.crypto_util.encrypt(
        next(replies),
        [
            current_app.crypto_util.get_fingerprint(source.filesystem_id),
            config.JOURNALIST_KEY,
        ],
        current_app.storage.path(source.filesystem_id, fname),
    )

    reply = Reply(journalist, source, fname)
    db.session.add(reply)
    db.session.flush()

    # Journalist who replied has seen the reply
    author_seen_reply = SeenReply(reply_id=reply.id, journalist_id=journalist.id)
    db.session.add(author_seen_reply)

    if journalist_who_saw:
        other_seen_reply = SeenReply(
            reply_id=reply.id, journalist_id=journalist_who_saw.id
        )
        db.session.add(other_seen_reply)

    db.session.commit()


def add_source() -> Tuple[Source, str]:
    """
    Adds a single source.
    """
    codename = PassphraseGenerator.get_default().generate_passphrase()
    filesystem_id = current_app.crypto_util.hash_codename(codename)
    journalist_designation = current_app.crypto_util.display_id()
    source = Source(filesystem_id, journalist_designation)
    source.pending = False
    db.session.add(source)
    db.session.commit()

    # Create source directory in store
    os.mkdir(current_app.storage.path(source.filesystem_id))

    # Generate source key
    current_app.crypto_util.genkeypair(source.filesystem_id, codename)

    return source, codename


def star_source(source: Source) -> None:
    """
    Adds a SourceStar record for the source.
    """
    star = SourceStar(source, True)
    db.session.add(star)
    db.session.commit()


def load(args: argparse.Namespace) -> None:
    """
    Populate the database.
    """
    if not os.environ.get("SECUREDROP_ENV"):
        os.environ["SECUREDROP_ENV"] = "dev"

    app = journalist_app.create_app(config)
    with app.app_context():
        try:
            default_journalist = add_journalist("journalist", is_admin=True)
        except IntegrityError as e:
            db.session.rollback()
            if "UNIQUE constraint failed: journalists." in str(e):
                default_journalist = Journalist.query.filter_by(username="journalist").one()
            else:
                raise e

        try:
            dellsberg = add_journalist("dellsberg")
        except IntegrityError as e:
            db.session.rollback()
            if "UNIQUE constraint failed: journalists." in str(e):
                dellsberg = Journalist.query.filter_by(username="dellsberg").one()
            else:
                raise e

        try:
            journalist_to_be_deleted = add_journalist(
                username="clarkkent", first_name="Clark", last_name="Kent"
            )
        except IntegrityError as e:
            db.session.rollback()
            if 'UNIQUE constraint failed: journalists.' in str(e):
                journalist_to_be_deleted = Journalist.query.filter_by(username="clarkkent").one()
            else:
                raise e

        for i in range(1, args.journalist_count + 1):
            add_journalist()

        starred_sources_count = int(args.source_count * args.source_star_fraction)
        replied_sources_count = int(args.source_count * args.source_reply_fraction)

        for i in range(1, args.source_count + 1):
            source, codename = add_source()

            for _ in range(args.messages_per_source):
                journalist_who_saw = random.choice(
                    [default_journalist, dellsberg, None]
                )
                submit_message(source, journalist_who_saw)

            for _ in range(args.files_per_source):
                journalist_who_saw = random.choice(
                    [default_journalist, dellsberg, None]
                )
                submit_file(source, journalist_who_saw)

            if i <= starred_sources_count:
                star_source(source)

            reply_to_source = i <= replied_sources_count
            if reply_to_source:
                for _ in range(args.replies_per_source):
                    journalist_who_replied = random.choice(
                        [dellsberg, journalist_to_be_deleted]
                    )
                    journalist_who_saw = random.choice([default_journalist, None])
                    add_reply(source, journalist_who_replied, journalist_who_saw)

            print(
                "Source {}/{} (codename: '{}', journalist designation '{}') "
                "added (files: {}, messages: {}, replies: {}".format(
                    i,
                    args.source_count,
                    codename,
                    source.journalist_designation,
                    args.files_per_source,
                    args.messages_per_source,
                    args.replies_per_source if reply_to_source else 0,
                )
            )

        # delete one journalist
        db.session.delete(journalist_to_be_deleted)
        db.session.commit()


def arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        os.path.basename(__file__),
        description="Loads test data into the database",
    )
    parser.add_argument(
        "--journalist-count",
        type=non_negative_int,
        default=default_journalist_count(),
        help=("Number of journalists to create in addition to the default accounts"),
    )
    parser.add_argument(
        "--source-count",
        type=set_source_count,
        default=default_source_count(),
        help=(
            'Number of sources to create, or "ALL" to create a number sufficient to '
            "demonstrate all of our test strings."
        ),
    )
    parser.add_argument(
        "--messages-per-source",
        type=non_negative_int,
        default=1,
        help=("Number of submitted messages to create for each source"),
    )
    parser.add_argument(
        "--files-per-source",
        type=non_negative_int,
        default=1,
        help=("Number of submitted files to create for each source"),
    )
    parser.add_argument(
        "--replies-per-source",
        type=non_negative_int,
        default=1,
        help=("Number of replies to create for any source that receives replies"),
    )
    parser.add_argument(
        "--source-star-fraction",
        type=fraction,
        default=0.1,
        help=("Fraction of sources with stars"),
    )
    parser.add_argument(
        "--source-reply-fraction",
        type=fraction,
        default=0.75,
        help=("Fraction of sources with replies"),
    )
    return parser


if __name__ == "__main__":  # pragma: no cover
    load(arg_parser().parse_args())
