"""Add Key DB

Revision ID: 917b2c88e235
Revises: 12d994a9a845
Create Date: 2021-09-10 20:40:47.122501

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '917b2c88e235'
down_revision = '12d994a9a845'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'Keys',
        sa.Column('key', sa.String, primary_key=True),
        sa.Column('ownertid', sa.Integer),
        sa.Column('scopes', sa.String, server_default='[]')
    )

    with op.batch_alter_table('Users') as batch_op:
        batch_op.drop_column('keys')


def downgrade():
    op.drop_table('Keys')
    op.add_column('Users', sa.Column('keys', sa.String, server_default='[]'))
