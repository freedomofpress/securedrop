"""add checksum columns and revoke token table
Revision ID: b58139cfdc8c
Revises: f2833ac34bb6
Create Date: 2019-04-02 10:45:05.178481
"""
import os

import sqlalchemy as sa
from alembic import op

# raise the errors if we're not in production
raise_errors = os.environ.get("SECUREDROP_ENV", "prod") != "prod"

try:
    from journalist_app import create_app
    from models import Reply, Submission
    from sdconfig import config
    from store import Storage, queued_add_checksum_for_file
    from worker import create_queue
except:  # noqa
    if raise_errors:
        raise

# revision identifiers, used by Alembic.
revision = "b58139cfdc8c"
down_revision = "f2833ac34bb6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("replies", schema=None) as batch_op:
        batch_op.add_column(sa.Column("checksum", sa.String(length=255), nullable=True))

    with op.batch_alter_table("submissions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("checksum", sa.String(length=255), nullable=True))

    op.create_table(
        "revoked_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("journalist_id", sa.Integer(), nullable=True),
        sa.Column("token", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["journalist_id"], ["journalists.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )

    try:
        app = create_app(config)

        # we need an app context for the rq worker extension to work properly
        with app.app_context():
            conn = op.get_bind()
            query = sa.text(
                """SELECT submissions.id, sources.filesystem_id, submissions.filename
                               FROM submissions
                               INNER JOIN sources
                               ON submissions.source_id = sources.id
                            """
            )
            for (sub_id, filesystem_id, filename) in conn.execute(query):
                full_path = Storage.get_default().path(filesystem_id, filename)
                create_queue().enqueue(
                    queued_add_checksum_for_file,
                    Submission,
                    int(sub_id),
                    full_path,
                    app.config["SQLALCHEMY_DATABASE_URI"],
                )

            query = sa.text(
                """SELECT replies.id, sources.filesystem_id, replies.filename
                               FROM replies
                               INNER JOIN sources
                               ON replies.source_id = sources.id
                            """
            )
            for (rep_id, filesystem_id, filename) in conn.execute(query):
                full_path = Storage.get_default().path(filesystem_id, filename)
                create_queue().enqueue(
                    queued_add_checksum_for_file,
                    Reply,
                    int(rep_id),
                    full_path,
                    app.config["SQLALCHEMY_DATABASE_URI"],
                )
    except:  # noqa
        if raise_errors:
            raise


def downgrade() -> None:
    op.drop_table("revoked_tokens")

    with op.batch_alter_table("submissions", schema=None) as batch_op:
        batch_op.drop_column("checksum")

    with op.batch_alter_table("replies", schema=None) as batch_op:
        batch_op.drop_column("checksum")
