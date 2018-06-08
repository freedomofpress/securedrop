#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import os
import random
import string
import sys

from argparse import ArgumentParser
from datetime import datetime
from flask import current_app
from os import path
from sqlalchemy import text

from crypto_util import DICEWARE_SAFE_CHARS
from db import db
from journalist_app import create_app
from models import (Journalist, Source, Submission, SourceStar, Reply,
                    JournalistLoginAttempt)
from sdconfig import config as sdconfig

random.seed('~(=^–^)')  # mrow?

JOURNALIST_COUNT = 10
SOURCE_COUNT = 50


def random_bool():
    return bool(random.getrandbits(1))


def random_chars(len, nullable, chars=string.printable):
    if nullable and random_bool():
        return None
    else:
        return ''.join([random.choice(chars) for _ in range(len)])


def bool_or_none():
    return random.choice([True, False, None])


def random_datetime(nullable):
    if nullable and random_bool():
        return None
    else:
        return datetime(
            year=random.randint(1, 9999),
            month=random.randint(1, 12),
            day=random.randint(1, 28),
            hour=random.randint(0, 23),
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
            microsecond=random.randint(0, 1000),
        )


def new_journalist():
    # Make a diceware-like password
    pw = ' '.join([random_chars(3, nullable=False, chars=DICEWARE_SAFE_CHARS)
                   for _ in range(7)])
    journalist = Journalist(random_chars(random.randint(3, 32),
                                         nullable=False),
                            pw,
                            random_bool())
    if random_bool():
        # to add legacy passwords back in
        journalist.passphrase_hash = None
        journalist.pw_salt = random_chars(32, nullable=False)
        journalist.pw_hash = random_chars(64, nullable=False)

    journalist.is_admin = bool_or_none()

    journalist.is_totp = bool_or_none()
    journalist.hotp_counter = (random.randint(-1000, 1000)
                               if random_bool() else None)
    journalist.created_on = random_datetime(nullable=True)
    journalist.last_access = random_datetime(nullable=True)

    db.session.add(journalist)


def new_source():
    fid_len = random.randint(4, 32)
    designation_len = random.randint(4, 32)
    source = Source(random_chars(fid_len, nullable=False,
                                 chars=string.ascii_lowercase),
                    random_chars(designation_len, nullable=False))
    source.flagged = bool_or_none()
    source.last_updated = random_datetime(nullable=True)
    source.pending = False

    db.session.add(source)


def new_submission(config, source_id):
    source = Source.query.get(source_id)

    # A source may have a null fid according to the DB, but this will
    # break storage.path.
    if source.filesystem_id is None:
        return

    filename = fake_file(config, source.filesystem_id)
    submission = Submission(source, filename)

    # For issue #1189
    if random_bool():
        submission.source_id = None

    submission.downloaded = bool_or_none()

    db.session.add(submission)


def fake_file(config, source_fid):
    source_dir = path.join(config.STORE_DIR, source_fid)
    if not path.exists(source_dir):
        os.mkdir(source_dir)

    filename = random_chars(20, nullable=False, chars=string.ascii_lowercase)
    num = random.randint(0, 100)
    msg_type = 'msg' if random_bool() else 'doc.gz'
    filename = '{}-{}-{}.gpg'.format(num, filename, msg_type)
    f_len = int(math.floor(random.expovariate(100000) * 1024 * 1024 * 500))
    sub_path = current_app.storage.path(source_fid, filename)
    with open(sub_path, 'w') as f:
        f.write('x' * f_len)

    return filename


def new_source_star(source_id):
    source = Source.query.get(source_id)
    star = SourceStar(source, bool_or_none())
    db.session.add(star)


def new_reply(config, journalist_id, source_id):
    source = Source.query.get(source_id)

    # A source may have a null fid according to the DB, but this will
    # break storage.path.
    if source.filesystem_id is None:
        return

    journalist = Journalist.query.get(journalist_id)
    filename = fake_file(config, source.filesystem_id)
    reply = Reply(journalist, source, filename)
    db.session.add(reply)


def new_journalist_login_attempt(journalist_id):
    journalist = Journalist.query.get(journalist_id)
    attempt = JournalistLoginAttempt(journalist)
    attempt.timestamp = random_datetime(nullable=True)
    db.session.add(attempt)


def new_abandoned_submission(config, source_id):
    '''For issue #1189'''

    source = Source.query.filter(Source.filesystem_id.isnot(None)).all()[0]
    filename = fake_file(config, source.filesystem_id)

    # Use this as hack to create a real submission then swap out the source_id
    submission = Submission(source, filename)
    submission.source_id = source_id
    db.session.add(submission)
    db.session.commit()
    delete_source(source_id)


def delete_source(source_id):
    '''For issue #1189'''
    db.session.execute(text('DELETE FROM sources WHERE id = :source_id'),
                       {'source_id':  source_id})


def positive_int(s):
    i = int(s)
    if i < 1:
        raise ValueError('{} is not >= 1'.format(s))
    return i


def load_data(config, multiplier):
    app = create_app(config)

    with app.app_context():
        for _ in range(JOURNALIST_COUNT * multiplier):
            new_journalist()
        db.session.commit()

        for _ in range(SOURCE_COUNT * multiplier):
            new_source()
        db.session.commit()

        for sid in range(1, SOURCE_COUNT * multiplier, 5):
            for _ in range(1, multiplier + 1):
                new_submission(config, sid)
        db.session.commit()

        for sid in range(1, SOURCE_COUNT * multiplier, 5):
            new_source_star(sid)
        db.session.commit()

        for jid in range(1, JOURNALIST_COUNT * multiplier, 10):
            for sid in range(1, SOURCE_COUNT * multiplier, 10):
                for _ in range(1, 3):
                    new_reply(config, jid, sid)
        db.session.commit()

        for jid in range(1, JOURNALIST_COUNT * multiplier, 10):
            new_journalist_login_attempt(jid)
        db.session.commit()

        for sid in range(SOURCE_COUNT * multiplier,
                         SOURCE_COUNT * multiplier + multiplier):
            new_abandoned_submission(config, sid)


def arg_parser():
    parser = ArgumentParser(
        path.basename(__file__),
        description='Loads data into the database for testing upgrades')
    parser.add_argument('-m', '--multiplier', type=positive_int, default=100,
                        help=('Factor to multiply the loaded data by '
                              '(default 100)'))
    return parser


def main():
    args = arg_parser().parse_args()
    print('Loading data. This make take a while.')
    load_data(sdconfig, args.multiplier)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('')  # for prompt on a newline
        sys.exit(1)
