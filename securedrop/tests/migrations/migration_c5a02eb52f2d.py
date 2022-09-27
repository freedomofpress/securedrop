# -*- coding: utf-8 -*-
import random
import uuid

from db import db
from journalist_app import create_app
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from .helpers import random_chars


class Helper:
    def __init__(self):
        self.journalist_id = None


class UpgradeTester(Helper):
    def __init__(self, config):
        Helper.__init__(self)
        self.config = config
        self.app = create_app(config)

    def create_journalist(self):
        params = {
            "uuid": str(uuid.uuid4()),
            "username": random_chars(50),
            "nonce": random.randint(20, 100),
        }
        sql = """INSERT INTO journalists (uuid, username, session_nonce)
                 VALUES (:uuid, :username, :nonce)"""
        return db.engine.execute(text(sql), **params).lastrowid

    def add_revoked_token(self):
        params = {
            "journalist_id": self.journalist_id,
            "token": "abc123",
        }
        sql = """INSERT INTO revoked_tokens (journalist_id, token)
                 VALUES (:journalist_id, :token)
              """
        db.engine.execute(text(sql), **params)

    def load_data(self):
        with self.app.app_context():
            self.journalist_id = self.create_journalist()
            self.add_revoked_token()

    def check_upgrade(self):
        with self.app.app_context():
            sql = "SELECT session_nonce FROM journalists WHERE id = :id"
            params = {"id": self.journalist_id}
            try:
                db.engine.execute(text(sql), **params).fetchall()
            except OperationalError:
                pass
            sql = "SELECT * FROM revoked_tokens WHERE id = :id"
            try:
                db.engine.execute(text(sql), **params).fetchall()
            except OperationalError:
                pass


class DowngradeTester(Helper):
    def __init__(self, config):
        Helper.__init__(self)
        self.config = config
        self.app = create_app(config)

    def create_journalist(self):
        params = {"uuid": str(uuid.uuid4()), "username": random_chars(50)}
        sql = """INSERT INTO journalists (uuid, username)
                 VALUES (:uuid, :username)"""
        return db.engine.execute(text(sql), **params).lastrowid

    def load_data(self):
        with self.app.app_context():
            self.journalist_id = self.create_journalist()

    def check_downgrade(self):
        with self.app.app_context():
            sql = "SELECT session_nonce FROM journalists WHERE id = :id"
            params = {"id": self.journalist_id}
            res = db.engine.execute(text(sql), **params).fetchone()
            assert isinstance(res["session_nonce"], int)
            sql = """INSERT INTO revoked_tokens (journalist_id, token)
                   VALUES (:journalist_id, :token)"""
            params = {"journalist_id": self.journalist_id, "token": "abc789"}
            res = db.engine.execute(text(sql), **params).lastrowid
            assert isinstance(res, int)
