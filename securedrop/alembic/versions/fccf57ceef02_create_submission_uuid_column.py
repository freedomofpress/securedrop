"""create submission uuid column

Revision ID: fccf57ceef02
Revises: 3d91d6948753
Create Date: 2018-07-12 00:06:20.891213

"""
from alembic import op
import sqlalchemy as sa

import uuid

# revision identifiers, used by Alembic.
revision = "fccf57ceef02"
down_revision = "3d91d6948753"
branch_labels = None
depends_on = None


def upgrade():
    # Schema migration
    op.rename_table("submissions", "submissions_tmp")

    # Add UUID column.
    op.add_column("submissions_tmp", sa.Column("uuid", sa.String(length=36)))

    # Add UUIDs to submissions_tmp table.
    conn = op.get_bind()
    submissions = conn.execute(sa.text("SELECT * FROM submissions_tmp")).fetchall()

    for submission in submissions:
        conn.execute(
            sa.text(
                """UPDATE submissions_tmp SET uuid=:submission_uuid WHERE
                       id=:id"""
            ).bindparams(submission_uuid=str(uuid.uuid4()), id=submission.id)
        )

    # Now create new table with unique constraint applied.
    op.create_table(
        "submissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("downloaded", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )

    # Data Migration: move all submissions into the new table.
    conn.execute(
        """
        INSERT INTO submissions
        SELECT id, uuid, source_id, filename, size, downloaded
        FROM submissions_tmp
    """
    )

    # Now delete the old table.
    op.drop_table("submissions_tmp")


def downgrade():
    with op.batch_alter_table("submissions", schema=None) as batch_op:
        batch_op.drop_column("uuid")
