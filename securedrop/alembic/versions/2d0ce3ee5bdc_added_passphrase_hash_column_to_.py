"""added passphrase_hash column to journalists table

Revision ID: 2d0ce3ee5bdc
Revises: fccf57ceef02
Create Date: 2018-06-08 15:08:37.718268

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2d0ce3ee5bdc"
down_revision = "fccf57ceef02"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("journalists", sa.Column("passphrase_hash", sa.String(length=256), nullable=True))


def downgrade():
    # sqlite has no `drop column` command, so we recreate the original table
    # then load it from a temp table
    conn = op.get_bind()
    conn.execute("PRAGMA legacy_alter_table=ON")
    op.rename_table("journalists", "journalists_tmp")

    op.create_table(
        "journalists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("pw_salt", sa.Binary(), nullable=True),
        sa.Column("pw_hash", sa.Binary(), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=True),
        sa.Column("otp_secret", sa.String(length=16), nullable=True),
        sa.Column("is_totp", sa.Boolean(), nullable=True),
        sa.Column("hotp_counter", sa.Integer(), nullable=True),
        sa.Column("last_token", sa.String(length=6), nullable=True),
        sa.Column("created_on", sa.DateTime(), nullable=True),
        sa.Column("last_access", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )

    conn.execute(
        """
        INSERT INTO journalists
        SELECT id, username, pw_salt, pw_hash, is_admin, otp_secret, is_totp,
               hotp_counter, last_token, created_on, last_access
        FROM journalists_tmp
    """
    )

    op.drop_table("journalists_tmp")
