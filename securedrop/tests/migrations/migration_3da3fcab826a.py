# -*- coding: utf-8 -*-

import random
from uuid import uuid4

from sqlalchemy import text

from db import db
from journalist_app import create_app
from .helpers import random_bool, random_chars, random_datetime, bool_or_none


class UpgradeTester:

    """This migration verifies that any orphaned submission data from deleted
    sources is also deleted.
    """

    def __init__(self, config):
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        with self.app.app_context():
            self.add_source()

            # Add submissions with and without a source
            self.add_submission(1)
            self.add_submission(None)

            db.session.commit()

    @staticmethod
    def add_source():
        filesystem_id = random_chars(96) if random_bool() else None
        params = {
            'uuid': str(uuid4()),
            'filesystem_id': filesystem_id,
            'journalist_designation': random_chars(50),
            'flagged': bool_or_none(),
            'last_updated': random_datetime(nullable=True),
            'pending': bool_or_none(),
            'interaction_count': random.randint(0, 1000),
        }
        sql = '''INSERT INTO sources (uuid, filesystem_id,
                    journalist_designation, flagged, last_updated, pending,
                    interaction_count)
                 VALUES (:uuid, :filesystem_id, :journalist_designation,
                    :flagged, :last_updated, :pending, :interaction_count)
              '''
        db.engine.execute(text(sql), **params)

    @staticmethod
    def add_submission(source_id):
        params = {
            'uuid': str(uuid4()),
            'source_id': source_id,
            'filename': random_chars(50),
            'size': random.randint(0, 1024 * 1024 * 500),
            'downloaded': bool_or_none(),
        }
        sql = '''INSERT INTO submissions (uuid, source_id, filename, size,
                    downloaded)
                 VALUES (:uuid, :source_id, :filename, :size, :downloaded)
              '''
        db.engine.execute(text(sql), **params)

    def check_upgrade(self):
        with self.app.app_context():
            submissions = db.engine.execute(
                text('SELECT * FROM submissions')).fetchall()

            # Submission without a source should be deleted
            assert len(submissions) == 1
            assert submissions[0].source_id is not None


class DowngradeTester:

    def __init__(self, config):
        self.config = config

    def load_data(self):
        pass

    def check_downgrade(self):
        pass
