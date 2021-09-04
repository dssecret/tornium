"""Add withdrawal channel to vault config

Revision ID: 93990f8d02bc
Revises: ee83d98e513d
Create Date: 2021-09-04 09:46:37.826640

"""
import json

from database import session_local
from models.factionmodel import FactionModel


# revision identifiers, used by Alembic.
revision = '93990f8d02bc'
down_revision = 'ee83d98e513d'
branch_labels = None
depends_on = None


def upgrade():
    session = session_local()
    for faction in session.query(FactionModel).all():
        vault_config = json.loads(faction.vaultconfig)
        vault_config['withdrawal'] = 0
        faction.vaultconfig = json.dumps(vault_config)

    session.flush()


def downgrade():
    session = session_local()
    for faction in session.query(FactionModel).all():
        vault_config = json.loads(faction.vaultconfig)
        vault_config.pop('withdrawal')
        faction.vaultconfig = json.dumps(vault_config)

    session.flush()
