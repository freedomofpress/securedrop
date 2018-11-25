"""delete orphaned submissions

Revision ID: 3da3fcab826a
Revises: f2833ac34bb6
Create Date: 2018-11-25 19:40:25.873292

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3da3fcab826a'
down_revision = 'f2833ac34bb6'
branch_labels = None
depends_on = None


def upgrade():
    # Get all submissions with null source IDs
    conn = op.get_bind()
    replies = conn.execute(
        sa.text('SELECT id, source_id FROM submissions WHERE source_id IS NULL')
    ).fetchall()

    # Delete them
    for reply in replies:
        conn.execute(
            sa.text("""
                DELETE FROM submissions
                WHERE id=:id
            """).bindparams(id=reply.id)
        )


def downgrade():
    pass
