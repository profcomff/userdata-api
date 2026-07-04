"""Add param_alias table

Revision ID: 8b49f52e2c01
Revises: fc911d58459b
Create Date: 2026-05-16 12:10:00.000000

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '8b49f52e2c01'
down_revision = 'fc911d58459b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'param_alias',
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('param_id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('create_ts', sa.DateTime(), nullable=False),
        sa.Column('modify_ts', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['param_id'],
            ['param.id'],
        ),
        sa.ForeignKeyConstraint(
            ['source_id'],
            ['source.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )


def downgrade():
    op.drop_table('param_alias')
