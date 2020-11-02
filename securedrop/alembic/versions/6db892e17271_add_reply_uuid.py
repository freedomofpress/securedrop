"""add reply UUID

Revision ID: 6db892e17271
Revises: e0a525cbab83
Create Date: 2018-08-06 20:31:50.035066

"""
from alembic import op
import sqlalchemy as sa

import uuid

# revision identifiers, used by Alembic.
revision = "6db892e17271"
down_revision = "e0a525cbab83"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute("PRAGMA legacy_alter_table=ON")
    # Schema migration
    op.rename_table("replies", "replies_tmp")

    # Add new column.
    op.add_column("replies_tmp", sa.Column("uuid", sa.String(length=36)))

    # Populate new column in replies_tmp table.
    replies = conn.execute(sa.text("SELECT * FROM replies_tmp")).fetchall()

    for reply in replies:
        conn.execute(
            sa.text(
                """UPDATE replies_tmp SET uuid=:reply_uuid WHERE
                       id=:id"""
            ).bindparams(reply_uuid=str(uuid.uuid4()), id=reply.id)
        )

    # Now create new table with constraints applied to UUID column.
    op.create_table(
        "replies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("journalist_id", sa.Integer(), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("deleted_by_source", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["journalist_id"], ["journalists.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )

    # Data Migration: move all replies into the new table.
    conn.execute(
        """
        INSERT INTO replies
        SELECT id, uuid, journalist_id, source_id, filename, size,
            deleted_by_source
        FROM replies_tmp
    """
    )

    # Now delete the old table.
    op.drop_table("replies_tmp")


def downgrade():
    with op.batch_alter_table("replies", schema=None) as batch_op:
        batch_op.drop_column("uuid")

    # ### end Alembic commands ###
