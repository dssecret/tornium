"""Remove name and level from statmodel

Revision ID: 616b3532ca80
Revises: 0b3019b4629b
Create Date: 2021-08-09 13:05:36.647763

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '616b3532ca80'
down_revision = '0b3019b4629b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('Stats') as batch_op:
        batch_op.drop_column('name')
        batch_op.drop_column('level')


def downgrade():
    op.add_column('Stats', sa.Column('name', sa.String))
    op.add_column('Stats', sa.Column('level', sa.Integer))
