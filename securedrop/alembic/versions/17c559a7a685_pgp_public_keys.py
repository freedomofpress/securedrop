"""PGP public keys

Revision ID: 17c559a7a685
Revises: 811334d7105f
Create Date: 2023-09-21 12:33:56.550634

"""

import traceback

import pretty_bad_protocol as gnupg
import sqlalchemy as sa
from alembic import op
from encryption import EncryptionManager
from sdconfig import SecureDropConfig

import redwood

# revision identifiers, used by Alembic.
revision = "17c559a7a685"
down_revision = "811334d7105f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Migrate public keys from the GPG keyring into the SQLite database

    We iterate over all the secret keys in the keyring and see if we
    can identify the corresponding Source record. If we can, and it
    doesn't already have key material migrated, export the key and
    save it in the database.
    """
    config = SecureDropConfig.get_current()
    gpg = gnupg.GPG(
        binary="gpg2",
        homedir=str(config.GPG_KEY_DIR),
        options=["--pinentry-mode loopback", "--trust-model direct"],
    )
    # Source keys all have a secret key, so we can filter on that
    for keyinfo in gpg.list_keys(secret=True):
        if len(keyinfo["uids"]) > 1:
            # Source keys should only have one UID
            continue
        uid = keyinfo["uids"][0]
        search = EncryptionManager.SOURCE_KEY_UID_RE.search(uid)
        if not search:
            # Didn't match at all
            continue
        filesystem_id = search.group(2)
        # Check that it's a valid ID
        conn = op.get_bind()
        result = conn.execute(
            sa.text(
                """
                SELECT pgp_public_key, pgp_fingerprint
                FROM sources
                WHERE filesystem_id=:filesystem_id
                """
            ).bindparams(filesystem_id=filesystem_id)
        ).first()
        if result != (None, None):
            # Either not in the database or there's already some data in the DB.
            # In any case, skip.
            continue
        fingerprint = keyinfo["fingerprint"]
        try:
            public_key = gpg.export_keys(fingerprint)
            redwood.is_valid_public_key(public_key)
        except:  # noqa: E722
            # Exporting the key failed in some manner
            traceback.print_exc()
            continue

        # Save to database
        op.execute(
            sa.text(
                """
                UPDATE sources
                SET pgp_public_key=:pgp_public_key, pgp_fingerprint=:pgp_fingerprint
                WHERE filesystem_id=:filesystem_id
                """
            ).bindparams(
                pgp_public_key=public_key,
                pgp_fingerprint=fingerprint,
                filesystem_id=filesystem_id,
            )
        )


def downgrade() -> None:
    """
    This is a non-destructive operation, so it's not worth implementing a
    migration from database storage to GPG.
    """
