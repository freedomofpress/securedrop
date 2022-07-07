# -*- coding: utf-8 -*-

import random
import string
import uuid

from db import db
from journalist_app import create_app
from sqlalchemy import text
from sqlalchemy.exc import NoSuchColumnError

from .helpers import (
    bool_or_none,
    random_bool,
    random_bytes,
    random_chars,
    random_datetime,
    random_username,
)

random.seed("ᕕ( ᐛ )ᕗ")


def add_source():
    filesystem_id = random_chars(96) if random_bool() else None
    params = {
        "uuid": str(uuid.uuid4()),
        "filesystem_id": filesystem_id,
        "journalist_designation": random_chars(50),
        "flagged": bool_or_none(),
        "last_updated": random_datetime(nullable=True),
        "pending": bool_or_none(),
        "interaction_count": random.randint(0, 1000),
    }
    sql = """INSERT INTO sources (uuid, filesystem_id,
                journalist_designation, flagged, last_updated, pending,
                interaction_count)
             VALUES (:uuid, :filesystem_id, :journalist_designation,
                :flagged, :last_updated, :pending, :interaction_count)
          """
    db.engine.execute(text(sql), **params)


def add_journalist():
    if random_bool():
        otp_secret = random_chars(16, string.ascii_uppercase + "234567")
    else:
        otp_secret = None

    is_totp = random_bool()
    if is_totp:
        hotp_counter = 0 if random_bool() else None
    else:
        hotp_counter = random.randint(0, 10000) if random_bool() else None

    last_token = random_chars(6, string.digits) if random_bool() else None

    params = {
        "username": random_username(),
        "pw_salt": random_bytes(1, 64, nullable=True),
        "pw_hash": random_bytes(32, 64, nullable=True),
        "is_admin": bool_or_none(),
        "otp_secret": otp_secret,
        "is_totp": is_totp,
        "hotp_counter": hotp_counter,
        "last_token": last_token,
        "created_on": random_datetime(nullable=True),
        "last_access": random_datetime(nullable=True),
        "passphrase_hash": random_bytes(32, 64, nullable=True),
    }
    sql = """INSERT INTO journalists (username, pw_salt, pw_hash,
                is_admin, otp_secret, is_totp, hotp_counter, last_token,
                created_on, last_access, passphrase_hash)
             VALUES (:username, :pw_salt, :pw_hash, :is_admin,
                :otp_secret, :is_totp, :hotp_counter, :last_token,
                :created_on, :last_access, :passphrase_hash);
          """
    db.engine.execute(text(sql), **params)


class UpgradeTester:

    """This migration verifies that the deleted_by_source column now exists,
    and that the data migration completed successfully.
    """

    SOURCE_NUM = 200
    JOURNO_NUM = 20

    def __init__(self, config):
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        with self.app.app_context():
            for _ in range(self.JOURNO_NUM):
                add_journalist()

            add_source()

            for jid in range(1, self.JOURNO_NUM):
                self.add_reply(jid, 1)

            db.session.commit()

    @staticmethod
    def add_reply(journalist_id, source_id):
        params = {
            "journalist_id": journalist_id,
            "source_id": source_id,
            "filename": random_chars(50),
            "size": random.randint(0, 1024 * 1024 * 500),
        }
        sql = """INSERT INTO replies (journalist_id, source_id, filename,
                    size)
                 VALUES (:journalist_id, :source_id, :filename, :size)
              """
        db.engine.execute(text(sql), **params)

    def check_upgrade(self):
        with self.app.app_context():
            replies = db.engine.execute(text("SELECT * FROM replies")).fetchall()
            assert len(replies) == self.JOURNO_NUM - 1

            for reply in replies:
                assert reply.deleted_by_source == False  # noqa


class DowngradeTester:

    SOURCE_NUM = 200
    JOURNO_NUM = 20

    def __init__(self, config):
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        with self.app.app_context():
            for _ in range(self.JOURNO_NUM):
                add_journalist()

            add_source()

            for jid in range(1, self.JOURNO_NUM):
                self.add_reply(jid, 1)

            db.session.commit()

    @staticmethod
    def add_reply(journalist_id, source_id):
        params = {
            "journalist_id": journalist_id,
            "source_id": source_id,
            "filename": random_chars(50),
            "size": random.randint(0, 1024 * 1024 * 500),
            "deleted_by_source": False,
        }
        sql = """INSERT INTO replies (journalist_id, source_id, filename,
                    size, deleted_by_source)
                 VALUES (:journalist_id, :source_id, :filename, :size,
                    :deleted_by_source)
              """
        db.engine.execute(text(sql), **params)

    def check_downgrade(self):
        """Verify that the deleted_by_source column is now gone, and
        otherwise the table has the expected number of rows.
        """
        with self.app.app_context():
            sql = "SELECT * FROM replies"
            replies = db.engine.execute(text(sql)).fetchall()

            for reply in replies:
                try:
                    # This should produce an exception, as the column (should)
                    # be gone.
                    assert reply["deleted_by_source"] is None
                except NoSuchColumnError:
                    pass

            assert len(replies) == self.JOURNO_NUM - 1
