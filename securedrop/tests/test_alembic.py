# -*- coding: utf-8 -*-

import os
import pytest
import subprocess

from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory
from os import path

MIGRATION_PATH = path.join(path.dirname(__file__), '..', 'alembic', 'versions')

ALL_MIGRATIONS = [x.split('.')[0]
                  for x in os.listdir(MIGRATION_PATH)
                  if x.endswith('.py')]


def list_migrations(cfg_path, head):
    cfg = AlembicConfig(cfg_path)
    script = ScriptDirectory.from_config(cfg)
    migrations = [x.revision
                  for x in script.walk_revisions(base='base', head=head)]
    migrations.reverse()
    return migrations


@pytest.mark.parametrize('migration',
                         [x.split('_')[0] for x in ALL_MIGRATIONS])
def test_alembic_migration_upgrade(alembic_config, config, migration):
    # run migrations in sequence from base -> head
    for mig in list_migrations(alembic_config, migration):
        subprocess.check_call(('cd {} && alembic upgrade {}'
                               .format(path.dirname(alembic_config),
                                       mig)),
                              shell=True)  # nosec


@pytest.mark.parametrize('migration',
                         [x.split('_')[0] for x in ALL_MIGRATIONS])
def test_alembic_migration_downgrade(alembic_config, config, migration):
    # upgrade to the parameterized test case ("head")
    subprocess.check_call(('cd {} && alembic upgrade {}'
                           .format(path.dirname(alembic_config),
                                   migration)),
                          shell=True)  # nosec

    # run migrations in sequence from "head" -> base
    migrations = list_migrations(alembic_config, migration)
    migrations.reverse()

    for mig in migrations:
        subprocess.check_call(('cd {} && alembic downgrade {}'
                               .format(path.dirname(alembic_config),
                                       mig)),
                              shell=True)  # nosec
