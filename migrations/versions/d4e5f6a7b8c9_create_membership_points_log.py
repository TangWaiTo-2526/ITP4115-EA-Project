"""create membership_points_log table

Revision ID: d4e5f6a7b8c9
Revises: a1b2c3d4e5f6
Create Date: 2026-04-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'd4e5f6a7b8c9'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'membership_points_log',
        sa.Column('points_log_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('retailer', sa.String(length=64), nullable=False),
        sa.Column('store_name', sa.String(length=128), nullable=False),
        sa.Column('transaction_amount_hkd', sa.Numeric(10, 2), nullable=False),
        sa.Column('base_points', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('extra_points', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('redeemed_points', sa.Integer(), nullable=True),
        sa.Column('create_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_uuid'], ['user.user_uuid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('points_log_uuid'),
    )

    op.create_index('ix_membership_points_log_user_uuid', 'membership_points_log', ['user_uuid'], unique=False)
    op.create_index('ix_membership_points_log_transaction_time', 'membership_points_log', ['transaction_time'], unique=False)


def downgrade():
    op.drop_index('ix_membership_points_log_transaction_time', table_name='membership_points_log')
    op.drop_index('ix_membership_points_log_user_uuid', table_name='membership_points_log')
    op.drop_table('membership_points_log')
