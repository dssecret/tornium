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
        op.add_column('Stats', sa.Column('globalstat', sa.Boolean, default=False))
        op.add_column('Stats', sa.Column('addedfactiontid', sa.Integer))
    else:
        op.add_column('Stats', sa.Column('globalstat', mysql.BOOLEAN, default=False))
        op.add_column('Stats', sa.Column('addedfactiontid', mysql.INTEGER))
    
    session = session_local()
    
    for stat in session.query(StatModel).all():
        user = User(stat.addedid)
        faction = Faction(user.factiontid)
        
        if json.loads(faction.statconfig)['global'] == 1:
            stat.globalstat = True
            stat.addedfactiontid = faction.tid
    
    session.flush()


def downgrade():
    with op.batch_alter_table('Stats') as batch_op:
        batch_op.drop_column('globalstat')
