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


class UpgradeTester:

    """This migration verifies that the UUID column now exists, and that
    the data migration completed successfully.
    """

    JOURNO_NUM = 20

    def __init__(self, config):
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        with self.app.app_context():
            for _ in range(self.JOURNO_NUM):
                self.add_journalist()
            db.session.commit()

    @staticmethod
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

    def check_upgrade(self):
        with self.app.app_context():
            journalists = db.engine.execute(text("SELECT * FROM journalists")).fetchall()

            for journalist in journalists:
                assert journalist.uuid is not None


class DowngradeTester:

    JOURNO_NUM = 20

    def __init__(self, config):
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        with self.app.app_context():
            for _ in range(self.JOURNO_NUM):
                self.add_journalist()
            db.session.commit()

    @staticmethod
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
            "uuid": str(uuid.uuid4()),
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
        sql = """INSERT INTO journalists (username, uuid, pw_salt, pw_hash,
                    is_admin, otp_secret, is_totp, hotp_counter, last_token,
                    created_on, last_access, passphrase_hash)
                 VALUES (:username, :uuid, :pw_salt, :pw_hash, :is_admin,
                    :otp_secret, :is_totp, :hotp_counter, :last_token,
                    :created_on, :last_access, :passphrase_hash);
              """
        db.engine.execute(text(sql), **params)

    def check_downgrade(self):
        """Verify that the UUID column is now gone, but otherwise the table
        has the expected number of rows.
        """
        with self.app.app_context():
            sql = "SELECT * FROM journalists"
            journalists = db.engine.execute(text(sql)).fetchall()

            for journalist in journalists:
                try:
                    # This should produce an exception, as the column (should)
                    # be gone.
                    assert journalist["uuid"] is None
                except NoSuchColumnError:
                    pass
