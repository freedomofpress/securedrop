# -*- coding: utf-8 -*-

import random
import uuid

from db import db
from journalist_app import create_app
from sqlalchemy import text
from sqlalchemy.exc import NoSuchColumnError

from .helpers import bool_or_none, random_bool, random_chars, random_datetime

random.seed("ᕕ( ᐛ )ᕗ")


class UpgradeTester:

    """This migration verifies that the UUID column now exists, and that
    the data migration completed successfully.
    """

    SOURCE_NUM = 200

    def __init__(self, config):
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        with self.app.app_context():

            for _ in range(self.SOURCE_NUM):
                self.add_source()

            db.session.commit()

    @staticmethod
    def add_source():
        filesystem_id = random_chars(96) if random_bool() else None
        params = {
            "filesystem_id": filesystem_id,
            "journalist_designation": random_chars(50),
            "flagged": bool_or_none(),
            "last_updated": random_datetime(nullable=True),
            "pending": bool_or_none(),
            "interaction_count": random.randint(0, 1000),
        }
        sql = """INSERT INTO sources (filesystem_id, journalist_designation,
                    flagged, last_updated, pending, interaction_count)
                 VALUES (:filesystem_id, :journalist_designation, :flagged,
                    :last_updated, :pending, :interaction_count)
              """
        db.engine.execute(text(sql), **params)

    def check_upgrade(self):
        with self.app.app_context():
            sources = db.engine.execute(text("SELECT * FROM sources")).fetchall()
            assert len(sources) == self.SOURCE_NUM

            for source in sources:
                assert source.uuid is not None


class DowngradeTester:

    SOURCE_NUM = 200

    def __init__(self, config):
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        with self.app.app_context():

            for _ in range(self.SOURCE_NUM):
                self.add_source()

            db.session.commit()

    @staticmethod
    def add_source():
        filesystem_id = random_chars(96) if random_bool() else None
        params = {
            "filesystem_id": filesystem_id,
            "uuid": str(uuid.uuid4()),
            "journalist_designation": random_chars(50),
            "flagged": bool_or_none(),
            "last_updated": random_datetime(nullable=True),
            "pending": bool_or_none(),
            "interaction_count": random.randint(0, 1000),
        }
        sql = """INSERT INTO sources (filesystem_id, uuid,
                    journalist_designation, flagged, last_updated, pending,
                    interaction_count)
                 VALUES (:filesystem_id, :uuid, :journalist_designation,
                    :flagged, :last_updated, :pending, :interaction_count)
              """
        db.engine.execute(text(sql), **params)

    def check_downgrade(self):
        """Verify that the UUID column is now gone, but otherwise the table
        has the expected number of rows.
        """
        with self.app.app_context():
            sql = "SELECT * FROM sources"
            sources = db.engine.execute(text(sql)).fetchall()

            for source in sources:
                try:
                    # This should produce an exception, as the column (should)
                    # be gone.
                    assert source["uuid"] is None
                except NoSuchColumnError:
                    pass

            assert len(sources) == self.SOURCE_NUM
