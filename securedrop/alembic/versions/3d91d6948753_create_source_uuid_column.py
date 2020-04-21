"""Create source UUID column

Revision ID: 3d91d6948753
Revises: faac8092c123
Create Date: 2018-07-09 22:39:05.088008

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import quoted_name
import uuid

# revision identifiers, used by Alembic.
revision = "3d91d6948753"
down_revision = "faac8092c123"
branch_labels = None
depends_on = None


def upgrade():
    # Schema migration
    op.rename_table("sources", "sources_tmp")

    # Add UUID column.
    op.add_column("sources_tmp", sa.Column("uuid", sa.String(length=36)))

    # Add UUIDs to sources_tmp table.
    conn = op.get_bind()
    sources = conn.execute(sa.text("SELECT * FROM sources_tmp")).fetchall()

    for source in sources:
        conn.execute(
            sa.text(
                """UPDATE sources_tmp SET uuid=:source_uuid WHERE
                       id=:id"""
            ).bindparams(source_uuid=str(uuid.uuid4()), id=source.id)
        )

    # Now create new table with unique constraint applied.
    op.create_table(
        quoted_name("sources", quote=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("filesystem_id", sa.String(length=96), nullable=True),
        sa.Column("journalist_designation", sa.String(length=255), nullable=False),
        sa.Column("flagged", sa.Boolean(), nullable=True),
        sa.Column("last_updated", sa.DateTime(), nullable=True),
        sa.Column("pending", sa.Boolean(), nullable=True),
        sa.Column("interaction_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
        sa.UniqueConstraint("filesystem_id"),
    )

    # Data Migration: move all sources into the new table.
    conn.execute(
        """
        INSERT INTO sources
        SELECT id, uuid, filesystem_id, journalist_designation, flagged,
               last_updated, pending, interaction_count
        FROM sources_tmp
    """
    )

    # Now delete the old table.
    op.drop_table("sources_tmp")


def downgrade():
    with op.batch_alter_table("sources", schema=None) as batch_op:
        batch_op.drop_column("uuid")
