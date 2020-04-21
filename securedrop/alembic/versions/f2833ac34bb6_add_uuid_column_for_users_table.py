"""add UUID column for users table

Revision ID: f2833ac34bb6
Revises: 6db892e17271
Create Date: 2018-08-13 18:10:19.914274

"""
from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision = "f2833ac34bb6"
down_revision = "6db892e17271"
branch_labels = None
depends_on = None


def upgrade():
    # Save existing journalist table.
    op.rename_table("journalists", "journalists_tmp")

    # Add UUID column.
    op.add_column("journalists_tmp", sa.Column("uuid", sa.String(length=36)))

    # Add UUIDs to journalists_tmp table.
    conn = op.get_bind()
    journalists = conn.execute(sa.text("SELECT * FROM journalists_tmp")).fetchall()

    for journalist in journalists:
        conn.execute(
            sa.text(
                """UPDATE journalists_tmp SET uuid=:journalist_uuid WHERE
                       id=:id"""
            ).bindparams(journalist_uuid=str(uuid.uuid4()), id=journalist.id)
        )

    # Now create new table with unique constraint applied.
    op.create_table(
        "journalists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("pw_salt", sa.Binary(), nullable=True),
        sa.Column("pw_hash", sa.Binary(), nullable=True),
        sa.Column("passphrase_hash", sa.String(length=256), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=True),
        sa.Column("otp_secret", sa.String(length=16), nullable=True),
        sa.Column("is_totp", sa.Boolean(), nullable=True),
        sa.Column("hotp_counter", sa.Integer(), nullable=True),
        sa.Column("last_token", sa.String(length=6), nullable=True),
        sa.Column("created_on", sa.DateTime(), nullable=True),
        sa.Column("last_access", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("uuid"),
    )

    conn = op.get_bind()
    conn.execute(
        """
        INSERT INTO journalists
        SELECT id, uuid, username, pw_salt, pw_hash, passphrase_hash,
               is_admin, otp_secret, is_totp, hotp_counter, last_token,
               created_on, last_access
        FROM journalists_tmp
    """
    )

    # Now delete the old table.
    op.drop_table("journalists_tmp")


def downgrade():
    with op.batch_alter_table("journalists", schema=None) as batch_op:
        batch_op.drop_column("uuid")
