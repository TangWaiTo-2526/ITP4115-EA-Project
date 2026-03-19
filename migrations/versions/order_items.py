"""create order_items table

Revision ID: e2d3c4b5a6f7
Revises: d1f2e3c4b5a6
Create Date: 2026-03-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'e2d3c4b5a6f7'
down_revision = 'd1f2e3c4b5a6'
branch_labels = None
depends_on = None


def upgrade():
    # 訂單明細表（order_items）
    op.create_table(
        'order_items',
        # 主鍵：訂單明細唯一識別符（UUID）
        sa.Column('order_item_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        # 所屬訂單
        sa.Column('order_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        # 商品明細
        sa.Column('product_details_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        # 購買數量
        sa.Column('quantity', sa.Integer(), nullable=False),
        # 單價
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        # 行小計
        sa.Column('line_total', sa.Numeric(10, 2), nullable=False),
        # 建立時間（預設 now()）
        sa.Column('create_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['order_uuid'], ['orders.order_uuid'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_details_uuid'], ['product_details.product_categories_uuid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('order_item_uuid'),
    )
    op.create_index('ix_order_items_order_uuid', 'order_items', ['order_uuid'], unique=False)
    op.create_index('ix_order_items_product_details_uuid', 'order_items', ['product_details_uuid'], unique=False)


def downgrade():
    op.drop_index('ix_order_items_product_details_uuid', table_name='order_items')
    op.drop_index('ix_order_items_order_uuid', table_name='order_items')
    op.drop_table('order_items')
