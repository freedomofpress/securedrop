# -*- coding: utf-8 -*-

import random
import string
from uuid import uuid4

from db import db
from journalist_app import create_app
from sqlalchemy import text

from .helpers import (
    bool_or_none,
    random_bool,
    random_bytes,
    random_chars,
    random_datetime,
    random_username,
)

random.seed("ᕕ( ᐛ )ᕗ")


class Helper:
    @staticmethod
    def add_source():
        filesystem_id = random_chars(96) if random_bool() else None
        params = {
            "uuid": str(uuid4()),
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

    @staticmethod
    def add_journalist_login_attempt(journalist_id):
        params = {
            "timestamp": random_datetime(nullable=True),
            "journalist_id": journalist_id,
        }
        sql = """INSERT INTO journalist_login_attempt (timestamp,
                    journalist_id)
                 VALUES (:timestamp, :journalist_id)
              """
        db.engine.execute(text(sql), **params)

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

    @staticmethod
    def extract(app):
        with app.app_context():
            sql = """SELECT j.id, count(distinct a.id), count(distinct r.id)
                     FROM journalists AS j
                     LEFT OUTER JOIN journalist_login_attempt AS a
                     ON a.journalist_id = j.id
                     LEFT OUTER JOIN replies AS r
                     ON r.journalist_id = j.id
                     GROUP BY j.id
                     ORDER BY j.id
                  """
            res = list(db.session.execute(text(sql)))
        return res


class UpgradeTester(Helper):

    JOURNO_NUM = 100

    def __init__(self, config):
        self.config = config
        self.app = create_app(config)
        self.initial_data = None

    def load_data(self):
        with self.app.app_context():
            for _ in range(self.JOURNO_NUM):
                self.add_journalist()

            self.add_source()

            for jid in range(1, self.JOURNO_NUM):
                for _ in range(random.randint(1, 3)):
                    self.add_journalist_login_attempt(jid)

            for jid in range(1, self.JOURNO_NUM):
                self.add_reply(jid, 1)

            db.session.commit()
            self.initial_data = self.extract(self.app)

    def check_upgrade(self):
        extracted = self.extract(self.app)
        assert len(extracted) == self.JOURNO_NUM
        assert extracted == self.initial_data

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
        }
        sql = """INSERT INTO journalists (username, pw_salt, pw_hash,
                    is_admin, otp_secret, is_totp, hotp_counter, last_token,
                    created_on, last_access)
                 VALUES (:username, :pw_salt, :pw_hash, :is_admin,
                    :otp_secret, :is_totp, :hotp_counter, :last_token,
                    :created_on, :last_access);
              """
        db.engine.execute(text(sql), **params)


class DowngradeTester(Helper):

    JOURNO_NUM = 100

    def __init__(self, config):
        self.config = config
        self.app = create_app(config)
        self.initial_data = None

    def load_data(self):
        with self.app.app_context():
            for _ in range(self.JOURNO_NUM):
                self.add_journalist()

            self.add_source()

            for jid in range(1, self.JOURNO_NUM):
                for _ in range(random.randint(1, 3)):
                    self.add_journalist_login_attempt(jid)

            for jid in range(1, self.JOURNO_NUM):
                self.add_reply(jid, 1)

            db.session.commit()
            self.initial_data = self.extract(self.app)

    def check_downgrade(self):
        extracted = self.extract(self.app)
        assert len(extracted) == self.JOURNO_NUM
        assert extracted == self.initial_data

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
