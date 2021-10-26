"""Revise stat DB
Revision ID: 943548ecd604
Revises: e679a249368c
Create Date: 2021-10-25 20:57:42.420550
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from database import session_local
from models.faction import Faction
from models.statmodel import StatModel
from models.user import User
from redisdb import get_redis


# revision identifiers, used by Alembic.
revision = '943548ecd604'
down_revision = 'e679a249368c'
branch_labels = None
depends_on = None


def upgrade():
    if get_redis().get('dev'):
        op.add_column('Stats', sa.Column('globalstat', sa.Boolean, server_default="0"))
        op.add_column('Stats', sa.Column('addedfactiontid', sa.Integer, server_default="0"))
    else:
        op.add_column('Stats', sa.Column('globalstat', mysql.BOOLEAN, server_default="0"))
        op.add_column('Stats', sa.Column('addedfactiontid', mysql.INTEGER, server_default="0"))

    session = session_local()
    max_stat = session.query(StatModel).count() - 1
    for stat in range(max_stat):
        stat = session.query(StatModel).filter_by(statid=stat).first()
        user = User(stat.addedid)
        faction = Faction(user.factiontid)

        if faction.stat_config['global'] == 1:
            stat.globalstat = 1
        else:
            stat.globalstat = 0
        stat.addedfactiontid = faction.tid
        session.flush()

    with op.batch_alter_table('Stats') as batch_op:
        batch_op.drop_column('battlestats')


def downgrade():
    with op.batch_alter_table('Stats') as batch_op:
        if get_redis().get('dev'):
            op.add_column('Stats', sa.Column('battlestats', sa.String, default='[0,0,0,0]'), )
        else:
            op.add_column('Stats', sa.Column('battlestats', mysql.TEXT, default='[0,0,0,0]'))

        batch_op.drop_column('globalstat')
        batch_op.drop_column('addedfactiontid')
