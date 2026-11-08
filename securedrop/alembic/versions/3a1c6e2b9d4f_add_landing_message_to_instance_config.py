"""add landing message to instance_config

Revision ID: 3a1c6e2b9d4f
Revises: b7f98cfd6a71
Create Date: 2026-11-08 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3a1c6e2b9d4f"
down_revision = "b7f98cfd6a71"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("instance_config", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("landing_message_enabled", sa.Boolean(), nullable=False, server_default="0")
        )
        batch_op.add_column(sa.Column("landing_message", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("instance_config", schema=None) as batch_op:
        batch_op.drop_column("landing_message")
        batch_op.drop_column("landing_message_enabled")
