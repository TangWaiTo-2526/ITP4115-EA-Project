"""create delivery table

Revision ID: f8g9h0i1j2k3
Revises: d4e5f6a7b8c9
Create Date: 2026-04-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'f8g9h0i1j2k3'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'delivery',
        sa.Column('delivery_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('deliver_time', sa.DateTime(), nullable=True),
        sa.Column('create_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['order_uuid'], ['orders.order_uuid'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_uuid'], ['user.user_uuid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('delivery_uuid'),
    )
    op.create_index('ix_delivery_order_uuid', 'delivery', ['order_uuid'], unique=False)
    op.create_index('ix_delivery_user_uuid', 'delivery', ['user_uuid'], unique=False)


def downgrade():
    op.drop_index('ix_delivery_user_uuid', table_name='delivery')
    op.drop_index('ix_delivery_order_uuid', table_name='delivery')
    op.drop_table('delivery')