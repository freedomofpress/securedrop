# -*- coding: utf-8 -*-
import io
import os
import random
import uuid
import mock

from os import path
from sqlalchemy import text
from sqlalchemy.exc import NoSuchColumnError

from db import db
from journalist_app import create_app
from store import Storage
from .helpers import random_chars, random_datetime

random.seed('ᕕ( ᐛ )ᕗ')

DATA = b'wat'
DATA_CHECKSUM = 'sha256:f00a787f7492a95e165b470702f4fe9373583fbdc025b2c8bdf0262cc48fcff4'


class Helper:

    def __init__(self):
        self.journalist_id = None
        self.source_id = None
        self._counter = 0

    @property
    def counter(self):
        self._counter += 1
        return self._counter

    def create_journalist(self):
        if self.journalist_id is not None:
            raise RuntimeError('Journalist already created')

        params = {
            'uuid': str(uuid.uuid4()),
            'username': random_chars(50),
        }
        sql = '''INSERT INTO journalists (uuid, username)
                 VALUES (:uuid, :username)
              '''
        self.journalist_id = db.engine.execute(text(sql), **params).lastrowid

    def create_source(self):
        if self.source_id is not None:
            raise RuntimeError('Source already created')

        self.source_filesystem_id = 'aliruhglaiurhgliaurg-{}'.format(self.counter)
        params = {
            'filesystem_id': self.source_filesystem_id,
            'uuid': str(uuid.uuid4()),
            'journalist_designation': random_chars(50),
            'flagged': False,
            'last_updated': random_datetime(nullable=True),
            'pending': False,
            'interaction_count': 0,
        }
        sql = '''INSERT INTO sources (filesystem_id, uuid, journalist_designation, flagged,
                    last_updated, pending, interaction_count)
                 VALUES (:filesystem_id, :uuid, :journalist_designation, :flagged, :last_updated,
                    :pending, :interaction_count)
              '''
        self.source_id = db.engine.execute(text(sql), **params).lastrowid

    def create_submission(self, checksum=False):
        filename = str(uuid.uuid4())
        params = {
            'uuid': str(uuid.uuid4()),
            'source_id': self.source_id,
            'filename': filename,
            'size': random.randint(10, 1000),
            'downloaded': False,

        }

        if checksum:
            params['checksum'] = \
                'sha256:f00a787f7492a95e165b470702f4fe9373583fbdc025b2c8bdf0262cc48fcff4'
            sql = '''INSERT INTO submissions (uuid, source_id, filename, size, downloaded, checksum)
                     VALUES (:uuid, :source_id, :filename, :size, :downloaded, :checksum)
                  '''
        else:
            sql = '''INSERT INTO submissions (uuid, source_id, filename, size, downloaded)
                     VALUES (:uuid, :source_id, :filename, :size, :downloaded)
                  '''

        return (db.engine.execute(text(sql), **params).lastrowid, filename)

    def create_reply(self, checksum=False):
        filename = str(uuid.uuid4())
        params = {
            'uuid': str(uuid.uuid4()),
            'source_id': self.source_id,
            'journalist_id': self.journalist_id,
            'filename': filename,
            'size': random.randint(10, 1000),
            'deleted_by_source': False,
        }

        if checksum:
            params['checksum'] = \
                'sha256:f00a787f7492a95e165b470702f4fe9373583fbdc025b2c8bdf0262cc48fcff4'
            sql = '''INSERT INTO replies (uuid, source_id, journalist_id, filename, size,
                        deleted_by_source, checksum)
                     VALUES (:uuid, :source_id, :journalist_id, :filename, :size,
                        :deleted_by_source, :checksum)
                  '''
        else:
            sql = '''INSERT INTO replies (uuid, source_id, journalist_id, filename, size,
                        deleted_by_source)
                     VALUES (:uuid, :source_id, :journalist_id, :filename, :size,
                        :deleted_by_source)
                  '''
        return (db.engine.execute(text(sql), **params).lastrowid, filename)


class UpgradeTester(Helper):

    def __init__(self, config):
        Helper.__init__(self)
        self.config = config
        self.app = create_app(config)

        # as this class requires access to the Storage object, which is no longer
        # attached to app, we create it here and mock the call to return it below.
        self.storage = Storage(config.STORE_DIR, config.TEMP_DIR)

    def load_data(self):
        global DATA
        with mock.patch("store.Storage.get_default") as mock_storage_global:
            mock_storage_global.return_value = self.storage
            with self.app.app_context():
                self.create_journalist()
                self.create_source()

                submission_id, submission_filename = self.create_submission()
                reply_id, reply_filename = self.create_reply()

                # we need to actually create files and write data to them so the
                # RQ worker can hash them
                for fn in [submission_filename, reply_filename]:
                    full_path = Storage.get_default().path(self.source_filesystem_id, fn)

                    dirname = path.dirname(full_path)
                    if not path.exists(dirname):
                        os.mkdir(dirname)

                    with io.open(full_path, 'wb') as f:
                        f.write(DATA)

    def check_upgrade(self):
        '''
        We cannot inject the `SDConfig` object provided by the fixture `config` into the alembic
        subprocess that actually performs the migration. This is needed to get both the value of the
        DB URL and access to the function `storage.path`. These values are passed to the `rqworker`,
        and without being able to inject this config, the checksum function won't succeed. The above
        `load_data` function provides data that can be manually verified by checking the `rqworker`
        log file in `/tmp/`.
        The other part of the migration, creating a table, cannot be tested regardless.
        '''
        pass


class DowngradeTester(Helper):

    def __init__(self, config):
        Helper.__init__(self)
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        with self.app.app_context():
            self.create_journalist()
            self.create_source()

            # create a submission and a reply that we don't add checksums to
            self.create_submission(checksum=False)
            self.create_reply(checksum=False)

            # create a submission and a reply that have checksums added
            self.create_submission(checksum=True)
            self.create_reply(checksum=True)

            # add a revoked token for enable a foreign key connection
            self.add_revoked_token()

    def check_downgrade(self):
        '''
        Verify that the checksum column is now gone.
        The dropping of the revoked_tokens table cannot be checked. If the migration completes,
        then it wokred correctly.
        '''
        with self.app.app_context():
            sql = "SELECT * FROM submissions"
            submissions = db.engine.execute(text(sql)).fetchall()
            for submission in submissions:
                try:
                    # this should produce an exception since the column is gone
                    submission['checksum']
                except NoSuchColumnError:
                    pass

            sql = "SELECT * FROM replies"
            replies = db.engine.execute(text(sql)).fetchall()
            for reply in replies:
                try:
                    # this should produce an exception since the column is gone
                    submission['checksum']
                except NoSuchColumnError:
                    pass

    def add_revoked_token(self):
        params = {
            'journalist_id': self.journalist_id,
            'token': 'abc123',
        }
        sql = '''INSERT INTO revoked_tokens (journalist_id, token)
                 VALUES (:journalist_id, :token)
              '''
        db.engine.execute(text(sql), **params)
