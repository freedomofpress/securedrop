from db import db
from journalist_app import create_app
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

instance_config_sql = "SELECT * FROM instance_config"


class UpgradeTester:
    def __init__(self, config):
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        pass

    def check_upgrade(self):
        with self.app.app_context():
            db.engine.execute(text(instance_config_sql)).fetchall()


class DowngradeTester:
    def __init__(self, config):
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        pass

    def check_downgrade(self):
        with self.app.app_context():
            try:
                db.engine.execute(text(instance_config_sql)).fetchall()

            # The SQLite driver appears to return this rather than the
            # expected NoSuchTableError.
            except OperationalError:
                pass
