import uuid

from db import db
from journalist_app import create_app
from sqlalchemy import text


class UpgradeTester:
    def __init__(self, config):
        self.config = config
        self.app = create_app(self.config)
        self.uuid = str(uuid.uuid4())

    def load_data(self):
        """Create a source"""
        with self.app.app_context():
            source = {
                "uuid": self.uuid,
                "filesystem_id": "5678",
                "journalist_designation": "alienated licensee",
                "interaction_count": 0,
            }
            sql = """\
                INSERT INTO sources (uuid, filesystem_id, journalist_designation,
                    interaction_count)
                VALUES (:uuid, :filesystem_id, :journalist_designation,
                    :interaction_count)"""
            db.engine.execute(text(sql), **source)

    def check_upgrade(self):
        """Verify PGP fields can be queried and modified"""
        with self.app.app_context():
            query_sql = """\
            SELECT pgp_fingerprint, pgp_public_key, pgp_secret_key
            FROM sources
            WHERE uuid = :uuid"""
            source = db.engine.execute(
                text(query_sql),
                uuid=self.uuid,
            ).fetchone()
            # Fields are set to NULL by default
            assert source == (None, None, None)
            update_sql = """\
            UPDATE sources
            SET pgp_fingerprint=:pgp_fingerprint, pgp_public_key=:pgp_public_key,
                pgp_secret_key=:pgp_secret_key
            WHERE uuid = :uuid"""
            db.engine.execute(
                text(update_sql),
                pgp_fingerprint="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                pgp_public_key="a public key!",
                pgp_secret_key="a secret key!",
                uuid=self.uuid,
            )
            source = db.engine.execute(text(query_sql), uuid=self.uuid).fetchone()
            # Fields are the values we set them to
            assert source == (
                "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "a public key!",
                "a secret key!",
            )


class DowngradeTester:
    def __init__(self, config):
        self.config = config
        self.app = create_app(self.config)
        self.uuid = str(uuid.uuid4())

    def load_data(self):
        """Create a source with a PGP key pair stored"""
        with self.app.app_context():
            source = {
                "uuid": self.uuid,
                "filesystem_id": "1234",
                "journalist_designation": "mucky pine",
                "interaction_count": 0,
                "pgp_fingerprint": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "pgp_public_key": "very public",
                "pgp_secret_key": "very secret",
            }
            sql = """\
                INSERT INTO sources (uuid, filesystem_id, journalist_designation,
                    interaction_count, pgp_fingerprint, pgp_public_key, pgp_secret_key)
                VALUES (:uuid, :filesystem_id, :journalist_designation,
                    :interaction_count, :pgp_fingerprint, :pgp_public_key, :pgp_secret_key)"""
            db.engine.execute(text(sql), **source)

    def check_downgrade(self):
        """Verify the downgrade does nothing, i.e. the PGP fields are still there"""
        with self.app.app_context():
            sql = """\
            SELECT pgp_fingerprint, pgp_public_key, pgp_secret_key
            FROM sources
            WHERE uuid = :uuid"""
            source = db.engine.execute(
                text(sql),
                uuid=self.uuid,
            ).fetchone()
            print(source)
            assert source == (
                "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "very public",
                "very secret",
            )
