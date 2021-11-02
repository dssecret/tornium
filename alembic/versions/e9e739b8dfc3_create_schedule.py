"""Create Schedule

Revision ID: e9e739b8dfc3
Revises: b0a79880c026
Create Date: 2021-10-05 16:20:17.072635

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e9e739b8dfc3'
down_revision = 'b0a79880c026'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'Schedules',
        sa.Column('uuid', sa.String, primary_key=True),
        sa.Column('factiontid', sa.Integer)
    )


def downgrade():
    op.drop_table('Schedules')
