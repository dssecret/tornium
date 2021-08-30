"""Add stat toggle to faction

Revision ID: 40d92b20d6e8
Revises: 616b3532ca80
Create Date: 2021-08-30 11:33:49.758776

"""
import json

from database import session_local
from models.factionmodel import FactionModel


# revision identifiers, used by Alembic.
revision = '40d92b20d6e8'
down_revision = '616b3532ca80'
branch_labels = None
depends_on = None


def upgrade():
    session = session_local()
    for faction in session.query(FactionModel).all():
        config = json.loads(faction.config)
        config['stat'] = 1
        faction.config = json.dumps(config)

    session.flush()


def downgrade():
    session = session_local()
    for faction in session.query(FactionModel).all():
        config = json.loads(faction.config)
        config.pop('stat')
        faction.config = json.dumps(config)

    session.flush()
