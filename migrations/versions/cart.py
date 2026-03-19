"""create cart table

Revision ID: f3e4d5c6b7a8
Revises: c9d4e27b1aa1
Create Date: 2026-03-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'f3e4d5c6b7a8'
down_revision = 'c9d4e27b1aa1'
branch_labels = None
depends_on = None


def upgrade():
    # 購物車表（cart），複合主鍵避免重複加入相同商品
    op.create_table(
        'cart',
        sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_details_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('create_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_uuid'], ['user.user_uuid'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_details_uuid'], ['product_details.product_categories_uuid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_uuid', 'product_details_uuid'),
    )


def downgrade():
    op.drop_table('cart')
