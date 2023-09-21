import uuid

import pretty_bad_protocol as gnupg
from db import db
from journalist_app import create_app
from sqlalchemy import text

import redwood


class UpgradeTester:
    def __init__(self, config):
        """This function MUST accept an argument named `config`.
        You will likely want to save a reference to the config in your
        class so you can access the database later.
        """
        self.config = config
        self.app = create_app(self.config)
        self.gpg = gnupg.GPG(
            binary="gpg2",
            homedir=str(config.GPG_KEY_DIR),
            options=["--pinentry-mode loopback", "--trust-model direct"],
        )
        self.fingerprint = None
        # random, chosen by fair dice roll
        self.filesystem_id = (
            "HAR5WIY3C4K3MMIVLYXER7DMTYCL5PWZEPNOCR2AIBCVWXDZQDMDFUHEFJM"
            "Z3JW5D6SLED3YKCBDAKNMSIYOKWEJK3ZRJT3WEFT3S5Q="
        )

    def load_data(self):
        """Create a source and GPG key pair"""
        with self.app.app_context():
            source = {
                "uuid": str(uuid.uuid4()),
                "filesystem_id": self.filesystem_id,
                "journalist_designation": "psychic webcam",
                "interaction_count": 0,
            }
            sql = """\
                INSERT INTO sources (uuid, filesystem_id, journalist_designation,
                    interaction_count)
                VALUES (:uuid, :filesystem_id, :journalist_designation,
                    :interaction_count)"""
            db.engine.execute(text(sql), **source)
            # Generate the GPG key pair
            gen_key_input = self.gpg.gen_key_input(
                passphrase="correct horse battery staple",
                name_email=self.filesystem_id,
                key_type="RSA",
                key_length=4096,
                name_real="Source Key",
                creation_date="2013-05-14",
                expire_date="0",
            )
            key = self.gpg.gen_key(gen_key_input)
            self.fingerprint = str(key.fingerprint)

    def check_upgrade(self):
        """Verify PGP fields have been populated"""
        with self.app.app_context():
            query_sql = """\
            SELECT pgp_fingerprint, pgp_public_key, pgp_secret_key
            FROM sources
            WHERE filesystem_id = :filesystem_id"""
            source = db.engine.execute(
                text(query_sql),
                filesystem_id=self.filesystem_id,
            ).fetchone()
            assert source[0] == self.fingerprint
            assert redwood.is_valid_public_key(source[1]) == self.fingerprint
            assert source[2] is None


class DowngradeTester:
    def __init__(self, config):
        self.config = config
        self.app = create_app(self.config)
        self.uuid = str(uuid.uuid4())

    def load_data(self):
        """Create a source with a PGP key pair already migrated"""
        with self.app.app_context():
            source = {
                "uuid": self.uuid,
                "filesystem_id": "1234",
                "journalist_designation": "mucky pine",
                "interaction_count": 0,
                "pgp_fingerprint": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "pgp_public_key": "very public",
                "pgp_secret_key": None,
            }
            sql = """\
                INSERT INTO sources (uuid, filesystem_id, journalist_designation,
                    interaction_count, pgp_fingerprint, pgp_public_key, pgp_secret_key)
                VALUES (:uuid, :filesystem_id, :journalist_designation,
                    :interaction_count, :pgp_fingerprint, :pgp_public_key, :pgp_secret_key)"""
            db.engine.execute(text(sql), **source)

    def check_downgrade(self):
        """Verify the downgrade does nothing, i.e. the two PGP fields are still populated"""
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
                None,
            )
