"""Added faction and user stakeouts

Revision ID: 96244bb57658
Revises: 40d92b20d6e8
Create Date: 2021-08-30 15:53:06.387760

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '96244bb57658'
down_revision = '40d92b20d6e8'
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.add_column('Servers', sa.Column('userstakeouts', sa.String, default='[]'))
        op.add_column('Servers', sa.Column('factionstakeouts', sa.String, default='[]'))
    except:
        pass

    op.create_table(
        'FactionStakeouts',
        sa.Column('tid', sa.Integer, primary_key=True),
        sa.Column('data', sa.String, default='{}'),
        sa.Column('guilds', sa.String, default='{}'),
        sa.Column('lastupdate', sa.Integer, default=0)
    )
    op.create_table(
        'UserStakeouts',
        sa.Column('tid', sa.Integer, primary_key=True),
        sa.Column('data', sa.String, default='{}'),
        sa.Column('guilds', sa.String, default='{}'),
        sa.Column('lastupdate', sa.Integer, default=0)
    )


def downgrade():
    with op.batch_alter_table('Servers') as batch_op:
        batch_op.drop_column('userstakeouts')
        batch_op.drop_column('factionstakeouts')

    op.drop_table('FactionStakeouts')
    op.drop_table('UserStakeouts')
