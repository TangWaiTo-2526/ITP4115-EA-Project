"""create orders table

Revision ID: d1f2e3c4b5a6
Revises: c9d4e27b1aa1
Create Date: 2026-03-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'd1f2e3c4b5a6'
down_revision = 'c9d4e27b1aa1'
branch_labels = None
depends_on = None


def upgrade():
    # 訂單主表（orders）
    op.create_table(
        'orders',
        # 主鍵：訂單唯一識別符（UUID）
        sa.Column('order_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        # 下單用戶（FK -> user.user_uuid）
        sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        # 訂單狀態
        sa.Column('order_status', sa.String(length=64), nullable=False),
        # 收件人
        sa.Column('receiver_name', sa.String(length=128), nullable=False),
        sa.Column('receiver_phone', sa.String(length=32), nullable=False),
        # 收貨地址快照
        sa.Column('receiver_address_snapshot', sa.Text(), nullable=False),
        # 訂單總價（貨幣）
        sa.Column('total_price', sa.Numeric(10, 2), nullable=False),
        # 建立時間（預設 now()）
        sa.Column('create_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_uuid'], ['user.user_uuid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('order_uuid'),
    )
    op.create_index('ix_orders_user_uuid', 'orders', ['user_uuid'], unique=False)
    op.create_index('ix_orders_create_time', 'orders', ['create_time'], unique=False)
    op.create_index('ix_orders_order_status', 'orders', ['order_status'], unique=False)


def downgrade():
    op.drop_index('ix_orders_order_status', table_name='orders')
    op.drop_index('ix_orders_create_time', table_name='orders')
    op.drop_index('ix_orders_user_uuid', table_name='orders')
    op.drop_table('orders')
