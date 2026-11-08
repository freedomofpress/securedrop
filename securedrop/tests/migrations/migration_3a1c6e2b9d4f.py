import pytest
import sqlalchemy
from db import db
from journalist_app import create_app
from sqlalchemy import text

from .helpers import random_bool, random_datetime


class UpgradeTester:
    def __init__(self, config):
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        with self.app.app_context():
            db.engine.execute(
                text(
                    "INSERT INTO instance_config (valid_until, allow_document_uploads) "
                    "VALUES (:valid_until, :allow_document_uploads)"
                ),
                valid_until=random_datetime(nullable=False),
                allow_document_uploads=random_bool(),
            )

    def check_upgrade(self):
        """Existing rows have the landing message disabled and unset."""
        with self.app.app_context():
            rows = db.engine.execute(
                text("SELECT landing_message_enabled, landing_message FROM instance_config")
            ).fetchall()
            assert rows
            for row in rows:
                assert row.landing_message_enabled == 0
                assert row.landing_message is None


class DowngradeTester:
    def __init__(self, config):
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        pass

    def check_downgrade(self):
        with self.app.app_context(), pytest.raises(sqlalchemy.exc.OperationalError):
            db.engine.execute(text("SELECT landing_message FROM instance_config")).fetchall()
