"""create refund table

Revision ID: h0i1j2k3l4m5
Revises: g9h0i1j2k3l4
Create Date: 2026-04-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'h0i1j2k3l4m5'
down_revision = 'g9h0i1j2k3l4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'refund',
        sa.Column('refund_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('create_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['order_uuid'], ['orders.order_uuid'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_uuid'], ['user.user_uuid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('refund_uuid'),
    )
    op.create_index('ix_refund_order_uuid', 'refund', ['order_uuid'], unique=False)
    op.create_index('ix_refund_user_uuid', 'refund', ['user_uuid'], unique=False)


def downgrade():
    op.drop_index('ix_refund_user_uuid', table_name='refund')
    op.drop_index('ix_refund_order_uuid', table_name='refund')
    op.drop_table('refund')