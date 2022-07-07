# -*- coding: utf-8 -*-

import pytest
import sqlalchemy
from db import db
from journalist_app import create_app

from .helpers import random_bool, random_datetime


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
            "valid_until": random_datetime(nullable=True),
            "allow_document_uploads": random_bool(),
        }
        sql = """
        INSERT INTO instance_config (
            valid_until, allow_document_uploads
        ) VALUES (
            :valid_until, :allow_document_uploads
        )
        """

        db.engine.execute(sqlalchemy.text(sql), **params)

    def check_upgrade(self):
        """
        Check the new `organization_name` column

        Querying `organization_name` shouldn't cause an error, but it should not yet be set.
        """
        with self.app.app_context():
            configs = db.engine.execute(
                sqlalchemy.text("SELECT * FROM instance_config WHERE organization_name IS NOT NULL")
            ).fetchall()
            assert len(configs) == 0


class DowngradeTester:
    def __init__(self, config):
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        pass

    def check_downgrade(self):
        """
        After downgrade, using `organization_name` in a query should raise an exception
        """
        with self.app.app_context():
            with pytest.raises(sqlalchemy.exc.OperationalError):
                configs = db.engine.execute(
                    sqlalchemy.text(
                        "SELECT * FROM instance_config WHERE organization_name IS NOT NULL"
                    )
                ).fetchall()
                assert len(configs) == 0
