# -*- coding: utf-8 -*-
import random
import uuid

from db import db
from journalist_app import create_app
from sqlalchemy import text

from .helpers import random_chars

random.seed("くコ:彡")


class Helper:
    def __init__(self):
        self.journalist_id = None

    def create_journalist(self, otp_secret="ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"):
        if self.journalist_id is not None:
            raise RuntimeError("Journalist already created")

        params = {
            "uuid": str(uuid.uuid4()),
            "username": random_chars(50),
            "session_nonce": 0,
            "otp_secret": otp_secret,
        }
        sql = """INSERT INTO journalists (uuid, username, otp_secret, session_nonce)
                 VALUES (:uuid, :username, :otp_secret, :session_nonce)
              """
        self.journalist_id = db.engine.execute(text(sql), **params).lastrowid


class UpgradeTester(Helper):
    """
    Checks schema to verify that the otp_secret varchar "length" has been updated.
    Varchar specified length isn't enforced by sqlite but it's good to verify that
    the migration worked as expected.
    """

    def __init__(self, config):
        Helper.__init__(self)
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        with self.app.app_context():
            self.create_journalist()

    def check_upgrade(self):
        with self.app.app_context():
            journalists_sql = "SELECT * FROM journalists"
            journalist = db.engine.execute(text(journalists_sql)).first()
            assert len(journalist["otp_secret"]) == 32  # Varchar ignores length


class DowngradeTester(Helper):
    def __init__(self, config):
        Helper.__init__(self)
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        with self.app.app_context():
            self.create_journalist()

    def check_downgrade(self):
        with self.app.app_context():
            journalists_sql = "SELECT * FROM journalists"
            journalist = db.engine.execute(text(journalists_sql)).first()
            assert len(journalist["otp_secret"]) == 32  # Varchar ignores length
