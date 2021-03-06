"""empty message

Revision ID: 7fc955d73f1e
Revises: 4dfffed89475
Create Date: 2020-04-23 14:17:09.632585

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7fc955d73f1e'
down_revision = '4dfffed89475'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('table', sa.Column('username', sa.String(length=64), nullable=True))
    op.drop_column('table', 'timestamp')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('table', sa.Column('timestamp', sa.DATETIME(), nullable=True))
    op.drop_column('table', 'username')
    # ### end Alembic commands ###
