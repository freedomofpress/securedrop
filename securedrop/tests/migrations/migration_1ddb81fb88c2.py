# -*- coding: utf-8 -*-

from db import db
from journalist_app import create_app
from sqlalchemy import text

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
            db.engine.execute(text("SELECT type, name, tbl_name, sql FROM sqlite_master"))
        )

    return ((x[0], x[1], x[2], x[3]) for x in result)


class UpgradeTester:
    """
    Ensure that the new index is created.
    """

    def __init__(self, config):
        self.app = create_app(config)

    def load_data(self):
        pass

    def check_upgrade(self):
        schema = get_schema(self.app)
        print(schema)
        assert index_definition in schema


class DowngradeTester:
    """
    Ensure that the new index is removed.
    """

    def __init__(self, config):
        self.app = create_app(config)

    def load_data(self):
        pass

    def check_downgrade(self):
        assert index_definition not in get_schema(self.app)
