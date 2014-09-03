"""empty message

Revision ID: 22cc65306494
Revises: 2e7581121dfb
Create Date: 2014-09-03 21:05:45.203254

"""

# revision identifiers, used by Alembic.
revision = '22cc65306494'
down_revision = '2e7581121dfb'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Users', sa.Column('height', sa.Numeric(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Users', 'height')
    ### end Alembic commands ###
