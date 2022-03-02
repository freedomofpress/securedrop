"""add message filtering

Revision ID: c89d9641d50c
Revises: 2e24fc7536e8
Create Date: 2022-03-01 21:56:50.038811

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c89d9641d50c'
down_revision = '2e24fc7536e8'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(sa.text('DROP INDEX IF EXISTS ix_one_active_instance_config'))
    with op.batch_alter_table('instance_config', schema=None) as batch_op:
        batch_op.add_column(sa.Column('initial_message_min_len', sa.Integer(), nullable=False,
                                      server_default=sa.text('0')))
        batch_op.add_column(sa.Column('reject_message_with_codename', sa.Boolean(), nullable=True))
    op.execute(sa.text('CREATE UNIQUE INDEX ix_one_active_instance_config ON instance_config '
                       '(valid_until IS NULL) WHERE valid_until IS NULL'))


def downgrade():
    op.execute(sa.text('DROP INDEX IF EXISTS ix_one_active_instance_config'))
    with op.batch_alter_table('instance_config', schema=None) as batch_op:
        batch_op.drop_column('reject_message_with_codename')
        batch_op.drop_column('initial_message_min_len')
    op.execute(sa.text('CREATE UNIQUE INDEX ix_one_active_instance_config ON instance_config '
                       '(valid_until IS NULL) WHERE valid_until IS NULL'))
