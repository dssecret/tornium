"""Add config to server

Revision ID: ee83d98e513d
Revises: 96244bb57658
Create Date: 2021-09-01 16:43:43.148858

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ee83d98e513d'
down_revision = '96244bb57658'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('Servers', sa.Column('config', sa.String, server_default='{"stakeouts": 0}'))
    op.add_column('Servers', sa.Column('stakeoutconfig', sa.String, server_default='{"category": 0}'))


def downgrade():
    with op.batch_alter_table('Servers') as batch_op:
        batch_op.drop_column('config')
        batch_op.drop_column('stakeoutconfig')
