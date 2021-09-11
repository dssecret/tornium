"""Add Tornium keys to usermodel

Revision ID: 12d994a9a845
Revises: 93990f8d02bc
Create Date: 2021-09-06 10:09:06.815541

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '12d994a9a845'
down_revision = '93990f8d02bc'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('Users', sa.Column('keys', sa.String, server_default='[]'))


def downgrade():
    with op.batch_alter_table('Users') as batch_op:
        batch_op.drop_column('keys')
