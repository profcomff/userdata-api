"""19 Added validtation column to Param

Revision ID: 0932ab8ca14a
Revises: f8c57101c0f6
Create Date: 2024-07-24 01:07:25.199873

"""

import sqlalchemy as sa
from alembic import op


revision = '0932ab8ca14a'
down_revision = 'f8c57101c0f6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('param', sa.Column('validation', sa.String(), nullable=True))


def downgrade():
    op.drop_column('param', 'validation')
