"""create product_details

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
Create Date: 2026-03-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'f3a4b5c6d7e8'
down_revision = 'e2f3a4b5c6d7'
branch_labels = None
depends_on = None


def upgrade():
    # 创建货物详情表：关联分类 + 供应商，记录商品名称、说明、价格、创建时间
    op.create_table(
        'product_details',
        sa.Column('product_categories_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_categories_id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('product_name', sa.String(length=128), nullable=False),
        sa.Column('product_details', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('create_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['product_categories_id'], ['product_categories.product_categories_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['supplier_id'], ['supplier.supplier_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('product_categories_uuid'),
    )
    op.create_index('ix_product_details_product_categories_id', 'product_details', ['product_categories_id'], unique=False)
    op.create_index('ix_product_details_supplier_id', 'product_details', ['supplier_id'], unique=False)


def downgrade():
    op.drop_index('ix_product_details_supplier_id', table_name='product_details')
    op.drop_index('ix_product_details_product_categories_id', table_name='product_details')
    op.drop_table('product_details')
