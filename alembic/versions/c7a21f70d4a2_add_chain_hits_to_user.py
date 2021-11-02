"""Add chain hits to user

Revision ID: c7a21f70d4a2
Revises: e9e739b8dfc3
Create Date: 2021-10-15 17:23:15.888271

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7a21f70d4a2'
down_revision = 'e9e739b8dfc3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('Users', sa.Column('chain_hits', sa.Integer))


def downgrade():
    with op.batch_alter_table('Users') as batch_op:
        batch_op.drop_column('chain_hits')
