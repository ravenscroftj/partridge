"""Added paper listeners/watchers table

Revision ID: 4abc902af771
Revises: 254c397fb9c5
Create Date: 2013-03-06 21:21:22.816434

"""

# revision identifiers, used by Alembic.
revision = '4abc902af771'
down_revision = '254c397fb9c5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('paper_watchers',
    sa.Column('filename', sa.String(length=50), nullable=False),
    sa.Column('email', sa.String(length=50), nullable=True),
    sa.PrimaryKeyConstraint('filename')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('paper_watchers')
    ### end Alembic commands ###
