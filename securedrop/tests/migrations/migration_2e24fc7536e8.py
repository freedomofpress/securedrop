import uuid

from db import db
from journalist_app import create_app
from sqlalchemy import text

from .helpers import random_datetime


class UpgradeTester:
    """Insert a Reply, SeenReply and JournalistLoginAttempt with journalist_id=NULL.
    Verify that the first two are reassociated to the "Deleted" user, while the last
    is deleted outright.
    """

    def __init__(self, config):
        """This function MUST accept an argument named `config`.
        You will likely want to save a reference to the config in your
        class, so you can access the database later.
        """
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        """This function loads data into the database and filesystem. It is
        executed before the upgrade.
        """
        with self.app.app_context():
            params = {
                "uuid": str(uuid.uuid4()),
                "journalist_id": None,
                "source_id": 0,
                "filename": "dummy.txt",
                "size": 1,
                "checksum": "",
                "deleted_by_source": False,
            }
            sql = """\
                INSERT INTO replies (uuid, journalist_id, source_id, filename,
                    size, checksum, deleted_by_source)
                 VALUES (:uuid, :journalist_id, :source_id, :filename,
                        :size, :checksum, :deleted_by_source);"""
            db.engine.execute(text(sql), **params)
            # Insert two SeenReplys corresponding to the just-inserted reply, which also
            # verifies our handling of duplicate keys.
            for _ in range(2):
                db.engine.execute(
                    text(
                        """\
                    INSERT INTO seen_replies (reply_id, journalist_id)
                    VALUES (1, NULL);
                    """
                    )
                )
            # Insert a JournalistLoginAttempt
            db.engine.execute(
                text(
                    """\
                INSERT INTO journalist_login_attempt (timestamp, journalist_id)
                VALUES (:timestamp, NULL)
                """
                ),
                timestamp=random_datetime(nullable=False),
            )

    def check_upgrade(self):
        """This function is run after the upgrade and verifies the state
        of the database or filesystem. It MUST raise an exception if the
        check fails.
        """
        with self.app.app_context():
            deleted = db.engine.execute(
                'SELECT id, passphrase_hash, otp_secret FROM journalists WHERE username="deleted"'
            ).first()
            # A passphrase_hash is set
            assert deleted[1].startswith("$argon2")
            # And a TOTP secret is set
            assert len(deleted[2]) == 32
            deleted_id = deleted[0]
            replies = db.engine.execute(text("SELECT journalist_id FROM replies")).fetchall()
            assert len(replies) == 1
            # And the journalist_id matches our "deleted" one
            assert replies[0][0] == deleted_id
            seen_replies = db.engine.execute(
                text("SELECT journalist_id FROM seen_replies")
            ).fetchall()
            assert len(seen_replies) == 1
            # And the journalist_id matches our "deleted" one
            assert seen_replies[0][0] == deleted_id
            login_attempts = db.engine.execute(
                text("SELECT * FROM journalist_login_attempt")
            ).fetchall()
            # The NULL login attempt was deleted outright
            assert login_attempts == []


class DowngradeTester:
    """Downgrading only makes fields nullable again, which is a
    non-destructive and safe operation"""

    def __init__(self, config):
        """This function MUST accept an argument named `config`.
        You will likely want to save a reference to the config in your
        class, so you can access the database later.
        """
        self.config = config

    def load_data(self):
        """This function loads data into the database and filesystem. It is
        executed before the downgrade.
        """
        pass

    def check_downgrade(self):
        """This function is run after the downgrade and verifies the state
        of the database or filesystem. It MUST raise an exception if the
        check fails.
        """
        pass
