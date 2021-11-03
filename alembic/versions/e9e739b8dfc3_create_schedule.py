"""Create Schedule

Revision ID: e9e739b8dfc3
Revises: e679a249368c
Create Date: 2021-10-05 16:20:17.072635

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from redisdb import get_redis


# revision identifiers, used by Alembic.
revision = 'e9e739b8dfc3'
down_revision = 'e679a249368c'
branch_labels = None
depends_on = None


def upgrade():
    if get_redis().get('dev'):
        op.create_table(
            'Schedules',
            sa.Column('uuid', sa.String, primary_key=True),
            sa.Column('factiontid', sa.Integer)
        )
    else:
        op.create_table(
            'Schedules',
            sa.Column('uuid', mysql.TEXT, primary_key=True),
            sa.Column('factiontid', mysql.INTEGER)
        )


def downgrade():
    op.drop_table('Schedules')
