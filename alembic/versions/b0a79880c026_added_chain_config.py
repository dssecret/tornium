"""Added Chain Config

Revision ID: b0a79880c026
Revises: 917b2c88e235
Create Date: 2021-09-29 21:14:45.543629

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b0a79880c026'
down_revision = '917b2c88e235'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('Factions', sa.Column('chainconfig', sa.String, server_default='{"od": 0, "odchannel": 0}'))
    op.add_column('Factions', sa.Column('chainod', sa.String, server_default='{}'))


def downgrade():
    with op.batch_alter_table('Factions') as batch_op:
        batch_op.drop_column('chainconfig')
        batch_op.drop_column('chainod')
