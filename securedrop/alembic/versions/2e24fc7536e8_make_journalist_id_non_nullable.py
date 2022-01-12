"""make journalist_id non-nullable

Revision ID: 2e24fc7536e8
Revises: de00920916bf
Create Date: 2022-01-12 19:31:06.186285

"""
from passlib.hash import argon2
import os
import pyotp
import uuid

from alembic import op
import sqlalchemy as sa

# raise the errors if we're not in production
raise_errors = os.environ.get("SECUREDROP_ENV", "prod") != "prod"

try:
    from models import ARGON2_PARAMS
    from passphrases import PassphraseGenerator
except:  # noqa
    if raise_errors:
        raise


# revision identifiers, used by Alembic.
revision = '2e24fc7536e8'
down_revision = 'de00920916bf'
branch_labels = None
depends_on = None


def generate_passphrase_hash() -> str:
    passphrase = PassphraseGenerator.get_default().generate_passphrase()
    return argon2.using(**ARGON2_PARAMS).hash(passphrase)


def create_deleted() -> int:
    """manually insert a "deleted" journalist user.

    We need to do it this way since the model will reflect the current state of
    the schema, not what it is at the current migration step

    It should be basically identical to what Journalist.get_deleted() does
    """
    op.execute(sa.text(
        """\
        INSERT INTO journalists (uuid, username, session_nonce, passphrase_hash, otp_secret)
        VALUES (:uuid, "deleted", 0, :passphrase_hash, :otp_secret);
        """
    ).bindparams(
        uuid=str(uuid.uuid4()),
        passphrase_hash=generate_passphrase_hash(),
        otp_secret=pyotp.random_base32(),
    ))
    # Get the autoincrement ID back
    conn = op.get_bind()
    result = conn.execute('SELECT id FROM journalists WHERE username="deleted";').fetchall()
    return result[0][0]


def migrate_nulls():
    """migrate existing journalist_id=NULL over to deleted or delete them"""
    op.execute("DELETE FROM journalist_login_attempt WHERE journalist_id IS NULL;")
    op.execute("DELETE FROM revoked_tokens WHERE journalist_id IS NULL;")
    # Look to see if we have data to migrate
    tables = ('replies', 'seen_files', 'seen_messages', 'seen_replies')
    needs_migration = []
    conn = op.get_bind()
    for table in tables:
        result = conn.execute(f'SELECT 1 FROM {table} WHERE journalist_id IS NULL;').first()  # nosec
        if result is not None:
            needs_migration.append(table)

    if not needs_migration:
        return

    deleted_id = create_deleted()
    for table in needs_migration:
        # The seen_ tables have UNIQUE(fk_id, journalist_id), so the deleted journalist can only have
        # seen each item once. It is possible multiple NULL journalist have seen the same thing so we
        # do this update in two passes.
        # First we update as many rows to point to the deleted journalist as possible, ignoring any
        # unique key violations.
        op.execute(sa.text(
            f'UPDATE OR IGNORE {table} SET journalist_id=:journalist_id WHERE journalist_id IS NULL;'
        ).bindparams(journalist_id=deleted_id))
        # Then we delete any leftovers which had been ignored earlier.
        op.execute(f'DELETE FROM {table} WHERE journalist_id IS NULL')  # nosec


def upgrade():
    migrate_nulls()

    with op.batch_alter_table('journalist_login_attempt', schema=None) as batch_op:
        batch_op.alter_column('journalist_id',
                              existing_type=sa.INTEGER(),
                              nullable=False)

    with op.batch_alter_table('replies', schema=None) as batch_op:
        batch_op.alter_column('journalist_id',
                              existing_type=sa.INTEGER(),
                              nullable=False)

    with op.batch_alter_table('revoked_tokens', schema=None) as batch_op:
        batch_op.alter_column('journalist_id',
                              existing_type=sa.INTEGER(),
                              nullable=False)

    with op.batch_alter_table('seen_files', schema=None) as batch_op:
        batch_op.alter_column('journalist_id',
                              existing_type=sa.INTEGER(),
                              nullable=False)

    with op.batch_alter_table('seen_messages', schema=None) as batch_op:
        batch_op.alter_column('journalist_id',
                              existing_type=sa.INTEGER(),
                              nullable=False)

    with op.batch_alter_table('seen_replies', schema=None) as batch_op:
        batch_op.alter_column('journalist_id',
                              existing_type=sa.INTEGER(),
                              nullable=False)


def downgrade():
    # We do not un-migrate the data back to journalist_id=NULL

    with op.batch_alter_table('seen_replies', schema=None) as batch_op:
        batch_op.alter_column('journalist_id',
                              existing_type=sa.INTEGER(),
                              nullable=True)

    with op.batch_alter_table('seen_messages', schema=None) as batch_op:
        batch_op.alter_column('journalist_id',
                              existing_type=sa.INTEGER(),
                              nullable=True)

    with op.batch_alter_table('seen_files', schema=None) as batch_op:
        batch_op.alter_column('journalist_id',
                              existing_type=sa.INTEGER(),
                              nullable=True)

    with op.batch_alter_table('revoked_tokens', schema=None) as batch_op:
        batch_op.alter_column('journalist_id',
                              existing_type=sa.INTEGER(),
                              nullable=True)

    with op.batch_alter_table('replies', schema=None) as batch_op:
        batch_op.alter_column('journalist_id',
                              existing_type=sa.INTEGER(),
                              nullable=True)

    with op.batch_alter_table('journalist_login_attempt', schema=None) as batch_op:
        batch_op.alter_column('journalist_id',
                              existing_type=sa.INTEGER(),
                              nullable=True)
