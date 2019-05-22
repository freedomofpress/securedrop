# -*- coding: utf-8 -*-
import random
import uuid

from sqlalchemy import text
from sqlalchemy.exc import NoSuchColumnError

from db import db
from journalist_app import create_app
from .helpers import random_chars

random.seed('⎦˚◡˚⎣')


class Helper:

    def __init__(self):
        self.journalist_id = None

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

    def create_journalist_after_migration(self):
        if self.journalist_id is not None:
            raise RuntimeError('Journalist already created')

        params = {
            'uuid': str(uuid.uuid4()),
            'username': random_chars(50),
            'first_name': random_chars(50),
            'last_name': random_chars(50)
        }
        sql = '''
        INSERT INTO journalists (uuid, username, first_name, last_name)
        VALUES (:uuid, :username, :first_name, :last_name)
        '''
        self.journalist_id = db.engine.execute(text(sql), **params).lastrowid


class UpgradeTester(Helper):

    def __init__(self, config):
        Helper.__init__(self)
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        with self.app.app_context():
            self.create_journalist()

    def check_upgrade(self):
        '''
        - Verify that Journalist first and last names are present after upgrade.
        '''
        with self.app.app_context():
            journalists_sql = "SELECT * FROM journalists"
            journalists = db.engine.execute(text(journalists_sql)).fetchall()
            for journalist in journalists:
                assert journalist['first_name'] is None
                assert journalist['last_name'] is None


class DowngradeTester(Helper):

    def __init__(self, config):
        Helper.__init__(self)
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        with self.app.app_context():
            self.create_journalist_after_migration()

    def check_downgrade(self):
        '''
        - Verify that Journalist first and last names are gone after downgrade.
        '''
        with self.app.app_context():
            journalists_sql = "SELECT * FROM journalists"
            journalists = db.engine.execute(text(journalists_sql)).fetchall()
            for journalist in journalists:
                try:
                    assert journalist['first_name']
                except NoSuchColumnError:
                    pass
                try:
                    assert journalist['last_name']
                except NoSuchColumnError:
                    pass
