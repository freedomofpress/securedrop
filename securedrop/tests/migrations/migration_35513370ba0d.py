# -*- coding: utf-8 -*-

import random
from uuid import uuid4

from db import db
from journalist_app import create_app
import sqlalchemy
import pytest

from .helpers import bool_or_none, random_bool, random_chars, random_datetime


class UpgradeTester:
    def __init__(self, config):
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        with self.app.app_context():
            self.add_source()
            self.valid_source_id = 1

            db.session.commit()

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
        sql = """
        INSERT INTO sources (
            uuid, filesystem_id, journalist_designation, flagged, last_updated,
            pending, interaction_count
        ) VALUES (
            :uuid, :filesystem_id, :journalist_designation, :flagged, :last_updated,
            :pending, :interaction_count
        )
        """

        db.engine.execute(sqlalchemy.text(sql), **params)

    def check_upgrade(self):
        """
        Check the new `deleted_at` column

        Querying `deleted_at` shouldn't cause an error, and no source
        should already have it set.
        """
        with self.app.app_context():
            sources = db.engine.execute(
                sqlalchemy.text("SELECT * FROM sources WHERE deleted_at IS NOT NULL")
            ).fetchall()
            assert len(sources) == 0


class DowngradeTester:
    def __init__(self, config):
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        pass

    def check_downgrade(self):
        """
        After downgrade, using `deleted_at` in a query should raise an exception
        """
        with self.app.app_context():
            with pytest.raises(sqlalchemy.exc.OperationalError):
                sources = db.engine.execute(
                    sqlalchemy.text(
                        "SELECT * FROM sources WHERE deleted_at IS NOT NULL"
                    )
                ).fetchall()
                assert len(sources) == 0
