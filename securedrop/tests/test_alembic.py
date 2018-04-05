# -*- coding: utf-8 -*-

import os
import pytest
import subprocess

from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory
from os import path
from sqlalchemy import text

from db import db
from journalist_app import create_app

MIGRATION_PATH = path.join(path.dirname(__file__), '..', 'alembic', 'versions')

ALL_MIGRATIONS = [x.split('.')[0].split('_')[0]
                  for x in os.listdir(MIGRATION_PATH)
                  if x.endswith('.py')]


def list_migrations(cfg_path, head):
    cfg = AlembicConfig(cfg_path)
    script = ScriptDirectory.from_config(cfg)
    migrations = [x.revision
                  for x in script.walk_revisions(base='base', head=head)]
    migrations.reverse()
    return migrations


def upgrade(alembic_config, migration):
    subprocess.check_call(('cd {} && alembic upgrade {}'
                           .format(path.dirname(alembic_config),
                                   migration)),
                          shell=True)  # nosec


def downgrade(alembic_config, migration):
    subprocess.check_call(('cd {} && alembic downgrade {}'
                           .format(path.dirname(alembic_config),
                                   migration)),
                          shell=True)  # nosec


def get_schema(app):
    with app.app_context():
        return list(db.engine.execute(text('''
            SELECT type, name, tbl_name, sql
            FROM sqlite_master
            ORDER BY type, name, tbl_name
            ''')))


@pytest.mark.parametrize('migration', ALL_MIGRATIONS)
def test_alembic_migration_upgrade(alembic_config, config, migration):
    # run migrations in sequence from base -> head
    for mig in list_migrations(alembic_config, migration):
        upgrade(alembic_config, mig)


@pytest.mark.parametrize('migration', ALL_MIGRATIONS)
def test_alembic_migration_downgrade(alembic_config, config, migration):
    # upgrade to the parameterized test case ("head")
    upgrade(alembic_config, migration)

    # run migrations in sequence from "head" -> base
    migrations = list_migrations(alembic_config, migration)
    migrations.reverse()

    for mig in migrations:
        downgrade(alembic_config, mig)


@pytest.mark.parametrize('migration', ALL_MIGRATIONS)
def test_schema_unchanged_after_up_then_downgrade(alembic_config,
                                                  config,
                                                  migration):
    # Create the app here. Using a fixture will init the database.
    app = create_app(config)

    migrations = list_migrations(alembic_config, migration)

    if len(migrations) > 1:
        target = migrations[-2]
        upgrade(alembic_config, target)
    else:
        # The first migration is the degenerate case where we don't need to
        # get the database to some base state.
        pass

    original_schema = get_schema(app)

    upgrade(alembic_config, '+1')
    downgrade(alembic_config, '-1')

    reverted_schema = get_schema(app)

    # The initial migration is a degenerate case because it creates the table
    # 'alembic_version', but rolling back the migration doesn't clear it.
    if len(migrations) == 1:
        reverted_schema = list(filter(lambda x: x[2] != 'alembic_version',
                                      reverted_schema))

    assert reverted_schema == original_schema
