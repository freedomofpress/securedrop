# -*- coding: utf-8 -*-

import random
import os
from uuid import uuid4

from sqlalchemy import text

from db import db
from journalist_app import create_app
from .helpers import random_bool, random_chars, random_ascii_chars, random_datetime, bool_or_none


TEST_DATA_DIR = '/tmp/securedrop/store'


def create_file_in_dummy_source_dir(filename):
    filesystem_id = 'dummy'
    basedir = os.path.join(TEST_DATA_DIR, filesystem_id)

    if not os.path.exists(basedir):
        os.makedirs(basedir)

    path_to_file = os.path.join(basedir, filename)
    with open(path_to_file, 'a'):
        os.utime(path_to_file, None)


class UpgradeTester:

    """This migration verifies that any orphaned submission or reply data from
    deleted sources is also deleted.
    """

    def __init__(self, config):
        self.config = config
        self.app = create_app(config)
        self.journalist_id = None

    def load_data(self):
        with self.app.app_context():
            self.create_journalist()
            self.add_source()
            self.valid_source_id = 1
            deleted_source_id = 2

            # Add submissions and replies with and without a valid source
            self.add_submission(self.valid_source_id)
            self.add_submission(deleted_source_id)
            self.add_submission(deleted_source_id, with_file=False)
            self.add_submission(None)  # NULL source

            self.add_reply(self.journalist_id, self.valid_source_id)
            self.add_reply(self.journalist_id, deleted_source_id)
            self.add_reply(self.journalist_id, deleted_source_id, with_file=False)
            self.add_reply(self.journalist_id, None)  # NULL source

            db.session.commit()

    def create_journalist(self):
        if self.journalist_id is not None:
            raise RuntimeError('Journalist already created')

        params = {
            'uuid': str(uuid4()),
            'username': random_chars(50),
            'session_nonce': 0
        }
        sql = '''INSERT INTO journalists (uuid, username, session_nonce)
                 VALUES (:uuid, :username, :session_nonce)
              '''
        self.journalist_id = db.engine.execute(text(sql), **params).lastrowid

    def add_reply(self, journalist_id, source_id, with_file=True):
        filename = '1-' + random_ascii_chars(5) + '-' + random_ascii_chars(5) + '-reply.gpg'
        params = {
            'uuid': str(uuid4()),
            'journalist_id': journalist_id,
            'source_id': source_id,
            'filename': filename,
            'size': random.randint(0, 1024 * 1024 * 500),
            'deleted_by_source': False,
        }
        sql = '''INSERT INTO replies (journalist_id, uuid, source_id, filename,
                    size, deleted_by_source)
                 VALUES (:journalist_id, :uuid, :source_id, :filename, :size,
                         :deleted_by_source)
              '''
        db.engine.execute(text(sql), **params)

        if with_file:
            create_file_in_dummy_source_dir(filename)

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

    def add_submission(self, source_id, with_file=True):
        filename = '1-' + random_ascii_chars(5) + '-' + random_ascii_chars(5) + '-doc.gz.gpg'
        params = {
            'uuid': str(uuid4()),
            'source_id': source_id,
            'filename': filename,
            'size': random.randint(0, 1024 * 1024 * 500),
            'downloaded': bool_or_none(),
        }
        sql = '''INSERT INTO submissions (uuid, source_id, filename, size,
                    downloaded)
                 VALUES (:uuid, :source_id, :filename, :size, :downloaded)
              '''
        db.engine.execute(text(sql), **params)

        if with_file:
            create_file_in_dummy_source_dir(filename)

    def check_upgrade(self):
        with self.app.app_context():
            submissions = db.engine.execute(
                text('SELECT * FROM submissions')).fetchall()

            # Submissions without a source should be deleted
            assert len(submissions) == 1
            for submission in submissions:
                assert submission.source_id == self.valid_source_id

            replies = db.engine.execute(
                text('SELECT * FROM replies')).fetchall()

            # Replies without a source should be deleted
            assert len(replies) == 1
            for reply in replies:
                assert reply.source_id == self.valid_source_id


class DowngradeTester:
    # This is a destructive alembic migration, it cannot be downgraded

    def __init__(self, config):
        self.config = config

    def load_data(self):
        pass

    def check_downgrade(self):
        pass
