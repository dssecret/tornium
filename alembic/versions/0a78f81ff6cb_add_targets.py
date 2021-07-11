"""Add targets

Revision ID: 0a78f81ff6cb
Revises: cdb5e74561d0
Create Date: 2021-07-09 21:04:16.420550

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0a78f81ff6cb'
down_revision = 'cdb5e74561d0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('Factions', sa.Column('targets', sa.String, server_default='{}'))


def downgrade():
    with op.batch_alter_table('Factions') as batch_op:
        batch_op.drop_column('targets')
