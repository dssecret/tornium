"""Add bot config column to faction model

Revision ID: cdb5e74561d0
Revises: d3624cdd6034
Create Date: 2021-07-09 13:47:17.998227

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cdb5e74561d0'
down_revision = 'd3624cdd6034'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('Factions', sa.Column('config', sa.String, server_default='{"vault": 0}'))


def downgrade():
    with op.batch_alter_table('Factions') as batch_op:
        batch_op.drop_column('config')
