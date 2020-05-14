#!/opt/venvs/securedrop-app-code/bin/python
# -*- coding: utf-8 -*-

import os
import random
import string
import sys
from argparse import ArgumentParser
from datetime import datetime
from itertools import cycle
from os import path

from flask import current_app

from crypto_util import DICEWARE_SAFE_CHARS
from db import db
from journalist_app import create_app
from models import Journalist, JournalistLoginAttempt, Reply, Source, SourceStar, Submission
from sdconfig import config as sdconfig


random.seed("~(=^–^)")  # mrow?


def random_bool():
    return bool(random.getrandbits(1))


def random_chars(len, nullable, chars=string.ascii_letters):
    if nullable and random_bool():
        return None
    else:
        return "".join([random.choice(chars) for _ in range(len)])


def bool_or_none():
    return random.choice([True, False, None])


def random_datetime(nullable):
    if nullable and random_bool():
        return None
    else:
        now = datetime.now()
        return datetime(
            year=random.randint(2013, now.year),
            month=random.randint(1, now.month),
            day=random.randint(1, now.day),
            hour=random.randint(0, 23),
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
            microsecond=random.randint(0, 1000),
        )


def positive_int(s):
    i = int(s)
    if i < 1:
        raise ValueError("{} is not >= 1".format(s))
    return i


def fraction(s):
    f = float(s)
    if 0 <= f <= 1:
        return f
    raise ValueError("{} should be a float between 0 and 1".format(s))


submissions = cycle(
    [
        "This is a test submission without markup!",
        'This is a test submission with markup and characters such as \, \\, \', " and ". '
        + "<strong>This text should not be bold</strong>!",  # noqa: W605, E501
    ]
)


replies = cycle(
    [
        "This is a test reply without markup!",
        'This is a test reply with markup and characters such as \, \\, \', " and ". '
        + "<strong>This text should not be bold</strong>!",  # noqa: W605, E501
    ]
)


class QaLoader(object):
    def __init__(
        self,
        config,
        journalist_count=10,
        source_count=50,
        submissions_per_source=1,
        replies_per_source=1,
        source_star_fraction=0.1,
        source_reply_fraction=0.5,
    ):
        """
        source_star_fraction and source_reply_fraction are simply the
        fraction of sources starred or replied to.
        """
        self.config = config
        self.app = create_app(config)

        self.journalist_count = journalist_count
        self.source_count = source_count
        self.submissions_per_source = submissions_per_source
        self.replies_per_source = replies_per_source
        self.source_star_fraction = source_star_fraction
        self.source_reply_fraction = source_reply_fraction

        self.journalists = []
        self.sources = []

    def new_journalist(self):
        # Make a diceware-like password
        pw = " ".join(
            [random_chars(3, nullable=False, chars=DICEWARE_SAFE_CHARS) for _ in range(7)]
        )
        journalist = Journalist(
            username=random_chars(random.randint(3, 32), nullable=False),
            password=pw,
            is_admin=random_bool(),
        )
        if random_bool():
            # to add legacy passwords back in
            journalist.passphrase_hash = None
            journalist.pw_salt = random_chars(32, nullable=False).encode("utf-8")
            journalist.pw_hash = random_chars(64, nullable=False).encode("utf-8")

        journalist.is_admin = bool_or_none()

        journalist.is_totp = bool_or_none()
        journalist.hotp_counter = random.randint(-1000, 1000) if random_bool() else None
        journalist.created_on = random_datetime(nullable=True)
        journalist.last_access = random_datetime(nullable=True)

        db.session.add(journalist)
        db.session.flush()
        self.journalists.append(journalist.id)

    def new_source(self):
        codename = current_app.crypto_util.genrandomid()
        filesystem_id = current_app.crypto_util.hash_codename(codename)
        journalist_designation = current_app.crypto_util.display_id()
        source = Source(filesystem_id, journalist_designation)
        db.session.add(source)
        db.session.flush()

        # Generate submissions directory and generate source key
        os.mkdir(current_app.storage.path(source.filesystem_id))
        current_app.crypto_util.genkeypair(source.filesystem_id, codename)

        self.sources.append(source.id)

    def new_submission(self, source_id):
        source = Source.query.get(source_id)

        source.interaction_count += 1
        fpath = current_app.storage.save_message_submission(
            source.filesystem_id,
            source.interaction_count,
            source.journalist_filename,
            next(submissions),
        )
        submission = Submission(source, fpath)
        db.session.add(submission)

        source.pending = False
        source.last_updated = datetime.utcnow()

        db.session.flush()

    def new_source_star(self, source_id):
        source = Source.query.get(source_id)
        star = SourceStar(source, bool_or_none())
        db.session.add(star)

    def new_reply(self, journalist_id, source_id):
        source = Source.query.get(source_id)

        journalist = Journalist.query.get(journalist_id)

        source.interaction_count += 1
        source.last_updated = datetime.utcnow()

        fname = "{}-{}-reply.gpg".format(source.interaction_count, source.journalist_filename)
        current_app.crypto_util.encrypt(
            next(replies),
            [
                current_app.crypto_util.get_fingerprint(source.filesystem_id),
                sdconfig.JOURNALIST_KEY
            ],
            current_app.storage.path(source.filesystem_id, fname),
        )

        reply = Reply(journalist, source, fname)
        db.session.add(reply)
        db.session.flush()

    def new_journalist_login_attempt(self, journalist_id):
        journalist = Journalist.query.get(journalist_id)
        attempt = JournalistLoginAttempt(journalist)
        attempt.timestamp = random_datetime(nullable=True)
        db.session.add(attempt)

    def load(self):
        with self.app.app_context():
            print("Creating {:d} journalists...".format(self.journalist_count))
            for i in range(1, self.journalist_count + 1):
                self.new_journalist()
                if i % min(10, max(1, int(self.journalist_count / 10))) == 0:
                    sys.stdout.write("{}\r{}".format(" " * len(str(self.journalist_count + 1)), i))
            print("\n")
            db.session.commit()

            print("Creating {:d} sources...".format(self.source_count))
            for i in range(1, self.source_count + 1):
                self.new_source()
                if i % min(10, max(1, int(self.source_count / 10))) == 0:
                    sys.stdout.write("{}\r{}".format(" " * len(str(self.source_count + 1)), i))
            print("\n")
            db.session.commit()

            print(
                "Creating submissions ({:d} each) for each source...".format(
                    self.submissions_per_source
                )
            )
            for sid in self.sources:
                for _ in range(1, self.submissions_per_source + 1):
                    self.new_submission(sid)
            db.session.commit()

            print("Starring {:.2f}% of all sources...".format(self.source_star_fraction * 100))
            for sid in random.sample(
                self.sources, int(self.source_count * self.source_star_fraction)
            ):
                self.new_source_star(sid)
            db.session.commit()

            print(
                "Creating replies ({:d} each) for {:.2f}% of sources...".format(
                    self.replies_per_source, self.source_reply_fraction * 100
                )
            )
            for sid in random.sample(
                self.sources, int(self.source_count * self.source_reply_fraction)
            ):
                jid = random.choice(self.journalists)
                for _ in range(self.replies_per_source):
                    self.new_reply(jid, sid)
            db.session.commit()

            for jid in self.journalists:
                self.new_journalist_login_attempt(jid)
            db.session.commit()


def arg_parser():
    parser = ArgumentParser(
        path.basename(__file__), description="Loads data into the database for testing upgrades"
    )
    parser.add_argument(
        "--journalist-count",
        type=positive_int,
        default=10,
        help=("Number of journalists to create"),
    )
    parser.add_argument(
        "--source-count", type=positive_int, default=50, help=("Number of sources to create")
    )
    parser.add_argument(
        "--submissions-per-source",
        type=positive_int,
        default=1,
        help=("Number of submissions to create for each source"),
    )
    parser.add_argument(
        "--replies-per-source",
        type=positive_int,
        default=1,
        help=("Number of replies to create for each source"),
    )
    parser.add_argument(
        "--source-star-fraction",
        type=fraction,
        default=0.1,
        help=("Fraction of sources to star"),
    )
    parser.add_argument(
        "--source-reply-fraction",
        type=fraction,
        default=0.5,
        help=("Fraction of sources to reply to"),
    )
    return parser


def main():
    args = arg_parser().parse_args()
    print("Loading data. This may take a while.")
    QaLoader(
        sdconfig,
        args.journalist_count,
        args.source_count,
        args.submissions_per_source,
        args.replies_per_source,
        args.source_star_fraction,
        args.source_reply_fraction,
    ).load()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("")  # for prompt on a newline
        sys.exit(1)
