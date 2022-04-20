"""add seen tables

Revision ID: 48a75abc0121
Revises: 35513370ba0d
Create Date: 2020-09-15 22:34:50.116403

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "48a75abc0121"
down_revision = "35513370ba0d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "seen_files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("journalist_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("file_id", "journalist_id"),
        sa.ForeignKeyConstraint(["file_id"], ["submissions.id"]),
        sa.ForeignKeyConstraint(["journalist_id"], ["journalists.id"]),
    )

    op.create_table(
        "seen_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("journalist_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", "journalist_id"),
        sa.ForeignKeyConstraint(["message_id"], ["submissions.id"]),
        sa.ForeignKeyConstraint(["journalist_id"], ["journalists.id"]),
    )

    op.create_table(
        "seen_replies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reply_id", sa.Integer(), nullable=False),
        sa.Column("journalist_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reply_id", "journalist_id"),
        sa.ForeignKeyConstraint(["reply_id"], ["replies.id"]),
        sa.ForeignKeyConstraint(["journalist_id"], ["journalists.id"]),
    )


def downgrade() -> None:
    op.drop_table("seen_files")
    op.drop_table("seen_messages")
    op.drop_table("seen_replies")
