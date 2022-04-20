"""Migrations for SecureDrop's 0.14.0 release

Revision ID: a9fe328b053a
Revises: b58139cfdc8c
Create Date: 2019-05-21 20:23:30.005632

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a9fe328b053a'
down_revision = 'b58139cfdc8c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('journalists', schema=None) as batch_op:
        batch_op.add_column(sa.Column('first_name', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('last_name', sa.String(length=255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('journalists', schema=None) as batch_op:
        batch_op.drop_column('last_name')
        batch_op.drop_column('first_name')
