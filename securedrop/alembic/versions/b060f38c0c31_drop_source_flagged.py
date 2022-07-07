"""drop Source.flagged

Revision ID: b060f38c0c31
Revises: 92fba0be98e9
Create Date: 2021-05-10 18:15:56.071880

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b060f38c0c31"
down_revision = "92fba0be98e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("sources", schema=None) as batch_op:
        batch_op.drop_column("flagged")


def downgrade() -> None:
    # You might be tempted to try Alembic's batch_ops for the
    # downgrade too. Don't. SQLite's unnamed check constraints require
    # kludges.

    conn = op.get_bind()
    conn.execute("PRAGMA legacy_alter_table=ON")

    op.rename_table("sources", "sources_tmp")

    conn.execute(
        sa.text(
            """
            CREATE TABLE "sources" (
                id INTEGER NOT NULL,
                uuid VARCHAR(36) NOT NULL,
                filesystem_id VARCHAR(96),
                journalist_designation VARCHAR(255) NOT NULL,
                last_updated DATETIME,
                pending BOOLEAN,
                interaction_count INTEGER NOT NULL,
                deleted_at DATETIME,
                flagged BOOLEAN,
                PRIMARY KEY (id),
                CHECK (pending IN (0, 1)),
                CHECK (flagged IN (0, 1)),
                UNIQUE (filesystem_id),
                UNIQUE (uuid)
            )
            """
        )
    )

    conn.execute(
        """
        INSERT INTO sources (
            id, uuid, filesystem_id, journalist_designation,
            last_updated, pending, interaction_count, deleted_at
        ) SELECT
            id, uuid, filesystem_id, journalist_designation,
            last_updated, pending, interaction_count, deleted_at
        FROM sources_tmp;
        """
    )

    # Now delete the old table.
    op.drop_table("sources_tmp")
