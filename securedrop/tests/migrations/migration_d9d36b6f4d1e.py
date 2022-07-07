# -*- coding: utf-8 -*-
import secrets

import pytest
import sqlalchemy
from db import db
from journalist_app import create_app

from .helpers import random_ascii_chars, random_bool, random_datetime

index_definition = (
    "index",
    "ix_one_active_instance_config",
    "instance_config",
    (
        "CREATE UNIQUE INDEX ix_one_active_instance_config "
        "ON instance_config (valid_until IS NULL) WHERE valid_until IS NULL"
    ),
)


def get_schema(app):
    with app.app_context():
        result = list(
            db.engine.execute(
                sqlalchemy.text("SELECT type, name, tbl_name, sql FROM sqlite_master")
            )
        )

    return ((x[0], x[1], x[2], x[3]) for x in result)


class UpgradeTester:
    def __init__(self, config):
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        with self.app.app_context():
            self.update_config()
            db.session.commit()

    @staticmethod
    def update_config():
        params = {
            "valid_until": random_datetime(nullable=False),
            "allow_document_uploads": random_bool(),
            "organization_name": random_ascii_chars(secrets.randbelow(75)),
        }
        sql = """
        INSERT INTO instance_config (
            valid_until, allow_document_uploads, organization_name
        ) VALUES (
            :valid_until, :allow_document_uploads, :organization_name
        )
        """

        db.engine.execute(sqlalchemy.text(sql), **params)

    def check_upgrade(self):
        schema = get_schema(self.app)
        print(schema)
        assert index_definition not in schema

        with self.app.app_context():
            for query in [
                "SELECT * FROM instance_config WHERE initial_message_min_len != 0",
                "SELECT * FROM instance_config WHERE reject_message_with_codename != 0",
            ]:
                result = db.engine.execute(sqlalchemy.text(query)).fetchall()
                assert len(result) == 0


class DowngradeTester:
    def __init__(self, config):
        self.app = create_app(config)

    def load_data(self):
        pass

    def check_downgrade(self):
        assert index_definition in get_schema(self.app)

        with self.app.app_context():
            for query in [
                "SELECT * FROM instance_config WHERE initial_message_min_len IS NOT NULL",
                "SELECT * FROM instance_config WHERE reject_message_with_codename IS NOT NULL",
            ]:
                with pytest.raises(sqlalchemy.exc.OperationalError):
                    db.engine.execute(sqlalchemy.text(query)).fetchall()
