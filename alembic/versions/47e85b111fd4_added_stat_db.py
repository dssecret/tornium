"""Added Spy DB

Revision ID: 47e85b111fd4
Revises: 0a78f81ff6cb
Create Date: 2021-07-17 15:37:09.419664

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '47e85b111fd4'
down_revision = '0a78f81ff6cb'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'Stats',
        sa.Column('tid', sa.Integer, primary_key=True),
        sa.Column('name', sa.String),
        sa.Column('battlescore', sa.Float),
        sa.Column('battlestats', sa.String, server_default='[]'),
        sa.Column('level', sa.Integer),
        sa.Column('timeadded', sa.Integer),
        sa.Column('addedid', sa.Integer)
    )

    op.add_column('Factions', sa.Column('statconfig', sa.String, server_default='{"global": 0}'))


def downgrade():
    op.drop_table('Stats')

    with op.batch_alter_table('Factions') as batch_op:
        batch_op.drop_column('statconfig')

