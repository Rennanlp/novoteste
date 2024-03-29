"""initial migration

Revision ID: cfb8203448c3
Revises: 
Create Date: 2024-02-22 16:46:58.363113

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cfb8203448c3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('task',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('task', sa.String(length=100), nullable=False),
    sa.Column('data', sa.String(length=20), nullable=False),
    sa.Column('observation', sa.String(length=255), nullable=True),
    sa.Column('qtd', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('task')
    # ### end Alembic commands ###
