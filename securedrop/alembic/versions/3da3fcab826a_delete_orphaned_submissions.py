"""delete orphaned submissions and replies

Ref: https://github.com/freedomofpress/securedrop/issues/1189

Revision ID: 3da3fcab826a
Revises: a9fe328b053a
Create Date: 2018-11-25 19:40:25.873292

"""
from alembic import op
import sqlalchemy as sa
from journalist_app import create_app
from models import Submission, Reply
from rm import srm
from sdconfig import config
from worker import rq_worker_queue

# revision identifiers, used by Alembic.
revision = '3da3fcab826a'
down_revision = 'a9fe328b053a'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    submissions = conn.execute(
        sa.text('SELECT id, filename, source_id FROM submissions WHERE source_id IS NULL')
    ).fetchall()

    replies = conn.execute(
        sa.text('SELECT id, filename, source_id FROM replies WHERE source_id IS NULL')
    ).fetchall()

    app = create_app(config)
    with app.app_context():
        for submission in submissions:
            file_path = app.storage.path_without_filesystem_id(submission.filename)
            rq_worker_queue.enqueue(srm, file_path)

            conn.execute(
            sa.text("""
                DELETE FROM submissions
                WHERE id=:id
            """).bindparams(id=submission.id)
            )

        for reply in replies:
            file_path = app.storage.path_without_filesystem_id(reply.filename)
            rq_worker_queue.enqueue(srm, file_path)

            conn.execute(
                sa.text("""
                    DELETE FROM replies
                    WHERE id=:id
                """).bindparams(id=reply.id)
            )


def downgrade():
    # This is a destructive alembic migration, it cannot be downgraded
    pass
