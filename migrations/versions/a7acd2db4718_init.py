"""Init

Revision ID: a7acd2db4718
Revises: 
Create Date: 2023-05-06 00:11:08.201100

"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'a7acd2db4718'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'category',
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('read_scope', sa.String(), nullable=True),
        sa.Column('update_scope', sa.String(), nullable=True),
        sa.Column('create_ts', sa.DateTime(), nullable=False),
        sa.Column('modify_ts', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'source',
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('trust_level', sa.Integer(), nullable=False),
        sa.Column('create_ts', sa.DateTime(), nullable=False),
        sa.Column('modify_ts', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'param',
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False),
        sa.Column('changeable', sa.Boolean(), nullable=False),
        sa.Column('type', sa.Enum('ALL', 'LAST', 'MOST_TRUSTED', name='viewtype', native_enum=False), nullable=False),
        sa.Column('create_ts', sa.DateTime(), nullable=False),
        sa.Column('modify_ts', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['category_id'],
            ['category.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'info',
        sa.Column('param_id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
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
    )


def downgrade():
    op.drop_table('info')
    op.drop_table('param')
    op.drop_table('source')
    op.drop_table('category')
