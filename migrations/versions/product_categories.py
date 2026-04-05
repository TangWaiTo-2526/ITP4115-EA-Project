"""create product_categories

Revision ID: d1e2f3a4b5c6
Revises: c9d4e27b1aa1
Create Date: 2026-03-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd1e2f3a4b5c6'
down_revision = 'c9d4e27b1aa1'
branch_labels = None
depends_on = None


def upgrade():
    # 创建货物分类表：分类 ID/名稱/父分類/層級/建立時間
    op.create_table(
        'product_categories',
        sa.Column('product_categories_id', sa.Integer(), nullable=False),
        sa.Column('product_categories_name', sa.String(length=128), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('create_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(
            ['parent_id'],
            ['product_categories.product_categories_id'],
            ondelete='CASCADE',
            name='fk_product_categories_parent_id',
        ),
        sa.PrimaryKeyConstraint('product_categories_id'),
        sa.UniqueConstraint('parent_id', 'product_categories_name', name='uq_product_category_parent_name'),
    )
    op.create_index('ix_product_categories_parent_id', 'product_categories', ['parent_id'], unique=False)


def downgrade():
    op.drop_index('ix_product_categories_parent_id', table_name='product_categories')
    op.drop_table('product_categories')
