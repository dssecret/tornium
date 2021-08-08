"""Add leader and coleader to faction

Revision ID: e679a249368c
Revises: 47e85b111fd4
Create Date: 2021-08-06 14:08:59.118243

"""
import json
import random

from alembic import op
import requests
import sqlalchemy as sa

from database import session_local
from models.factionmodel import FactionModel
from utils.tasks import tornget


# revision identifiers, used by Alembic.
revision = 'e679a249368c'
down_revision = '47e85b111fd4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('Factions', sa.Column('leader', sa.Integer))
    op.add_column('Factions', sa.Column('coleader', sa.Integer))

    session = session_local()
    requests_session = requests.Session()
    for faction in session.query(FactionModel).all():
        if len(json.loads(faction.keys)) == 0:
            continue
        faction_data = tornget(f'faction/{faction.tid}?selections=',
                               random.choice(json.loads(faction.keys)),
                               session=requests_session)
        faction_data = faction_data.get()
        faction.leader = faction_data['leader']
        faction.coleader = faction_data['co-leader']

    session.flush()


def downgrade():
    with op.batch_alter_table('Factions') as batch_op:
        batch_op.drop_column('leader')
        batch_op.drop_column('coleader')
