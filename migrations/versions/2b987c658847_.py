"""empty message

Revision ID: 2b987c658847
Revises: 13649c5960d0
Create Date: 2014-07-15 20:56:33.952553

"""

# revision identifiers, used by Alembic.
revision = '2b987c658847'
down_revision = '13649c5960d0'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('TargetValueChallenges',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('target_value', sa.Float(), nullable=True),
    sa.Column('unit', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['Challenges.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('DailyEvaluationChallenges',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('label_good', sa.String(length=30), nullable=True),
    sa.Column('label_marginal', sa.String(length=30), nullable=True),
    sa.Column('label_bad', sa.String(length=30), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['Challenges.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('TargetValueChallengeProgresses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('challenge_id', sa.Integer(), nullable=True),
    sa.Column('value', sa.Float(), nullable=True),
    sa.Column('timestamp', sa.Date(), nullable=True),
    sa.Column('note', sa.Text(length=500), nullable=True),
    sa.ForeignKeyConstraint(['challenge_id'], ['TargetValueChallenges.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.rename_table('Challenges', 'Challenges_Old')
    op.create_table('Challenges',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(length=10), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(length=50), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('start', sa.DateTime(), nullable=True),
    sa.Column('end', sa.DateTime(), nullable=True),
    sa.Column('points_success', sa.Float(), nullable=True),
    sa.Column('points_fail', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], [u'Users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    conn = op.get_bind()
    ch = table('Challenges',
               column('id', sa.Integer()),
               column('type', sa.String(length=10)),
               column('user_id', sa.Integer()),
               column('title', sa.String(length=50)),
               column('description', sa.Text()),
               column('start', sa.DateTime()),
               column('end', sa.DateTime()),
               column('points_success', sa.Float()),
               column('points_fail', sa.Float()),
              )
    ch_old = table('Challenges_Old',
                   column('id', sa.Integer()),
                   column('user_id', sa.Integer()),
                   column('title', sa.String(length=50)),
                   column('description', sa.Text()),
                   column('start', sa.DateTime()),
                   column('end', sa.DateTime()),
                   column('points_success', sa.Float()),
                   column('points_fail', sa.Float()),
                   column('target_value', sa.Float()),
                   column('unit', sa.String()),
                  )
    tv_ch = table('TargetValueChallenges',
                  column('id', sa.Integer()),
                  column('target_value', sa.Float()),
                  column('unit', sa.String(length=20)),
                 )
    for row in conn.execute(sa.select([ch_old])):
        to_insert = dict(row.items())
        del to_insert['unit']
        del to_insert['target_value']
        conn.execute(ch.insert().values(type='target_value', **to_insert))
        conn.execute(tv_ch.insert().values(id=row.id,
                                           target_value=row.target_value,
                                           unit=row.unit))


    ch_progress = table('ChallengeProgresses',
                        column('id', sa.Integer()),
                        column('challenge_id', sa.Integer()),
                        column('value', sa.Float()),
                        column('timestamp', sa.Date()),
                        column('note', sa.Text(length=500)),
                       )

    tv_progress = table('TargetValueChallengeProgresses',
                        column('id', sa.Integer()),
                        column('challenge_id', sa.Integer()),
                        column('value', sa.Float()),
                        column('timestamp', sa.Date()),
                        column('note', sa.Text(length=500)),
                       )

    for row in conn.execute(sa.select([ch_progress])).fetchall():
        conn.execute(tv_progress.insert().values(**row))

    op.drop_table('Challenges_Old')
    op.drop_table('ChallengeProgresses')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column(u'Challenges', sa.Column('unit', sa.VARCHAR(length=20), nullable=True))
    op.add_column(u'Challenges', sa.Column('target_value', sa.FLOAT(), nullable=True))
    op.drop_column(u'Challenges', 'type')
    op.create_table('ChallengeProgresses',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('challenge_id', sa.INTEGER(), nullable=True),
    sa.Column('value', sa.FLOAT(), nullable=True),
    sa.Column('timestamp', sa.DATE(), nullable=True),
    sa.Column('note', sa.TEXT(length=500), nullable=True),
    sa.ForeignKeyConstraint(['challenge_id'], [u'Challenges.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('TargetValueChallengeProgresses')
    op.drop_table('DailyEvaluationChallenges')
    op.drop_table('TargetValueChallenges')
    ### end Alembic commands ###
