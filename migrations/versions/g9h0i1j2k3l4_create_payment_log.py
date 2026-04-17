"""create payment_log table

Revision ID: g9h0i1j2k3l4
Revises: f8g9h0i1j2k3
Create Date: 2026-04-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'g9h0i1j2k3l4'
down_revision = 'f8g9h0i1j2k3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'payment_log',
        sa.Column('payment_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payment_methods', sa.String(length=64), nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('state', sa.String(length=64), nullable=False),
        sa.Column('create_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['order_uuid'], ['orders.order_uuid'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_uuid'], ['user.user_uuid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('payment_uuid'),
    )
    op.create_index('ix_payment_log_order_uuid', 'payment_log', ['order_uuid'], unique=False)
    op.create_index('ix_payment_log_user_uuid', 'payment_log', ['user_uuid'], unique=False)


def downgrade():
    op.drop_index('ix_payment_log_user_uuid', table_name='payment_log')
    op.drop_index('ix_payment_log_order_uuid', table_name='payment_log')
    op.drop_table('payment_log')