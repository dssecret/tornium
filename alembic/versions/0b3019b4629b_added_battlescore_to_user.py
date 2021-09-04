"""Added Battlescore to user

Revision ID: 0b3019b4629b
Revises: e679a249368c
Create Date: 2021-08-08 11:07:33.619628

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0b3019b4629b'
down_revision = 'e679a249368c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('Users', sa.Column('battlescore', sa.String, default='[]'))


def downgrade():
    with op.batch_alter_table('Users') as batch_op:
        batch_op.drop_column('battlescore')
