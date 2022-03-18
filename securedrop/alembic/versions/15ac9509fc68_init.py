"""init

Revision ID: 15ac9509fc68
Revises:
Create Date: 2018-03-30 21:20:58.280753

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "15ac9509fc68"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
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
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filesystem_id", sa.String(length=96), nullable=True),
        sa.Column("journalist_designation", sa.String(length=255), nullable=False),
        sa.Column("flagged", sa.Boolean(), nullable=True),
        sa.Column("last_updated", sa.DateTime(), nullable=True),
        sa.Column("pending", sa.Boolean(), nullable=True),
        sa.Column("interaction_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("filesystem_id"),
    )
    op.create_table(
        "journalist_login_attempt",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("journalist_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["journalist_id"], ["journalists.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "replies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("journalist_id", sa.Integer(), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["journalist_id"], ["journalists.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "source_stars",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("starred", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "submissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("downloaded", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("submissions")
    op.drop_table("source_stars")
    op.drop_table("replies")
    op.drop_table("journalist_login_attempt")
    op.drop_table("sources")
    op.drop_table("journalists")
