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
    # 创建货物分类表：分类 ID/名称/创建时间
    op.create_table(
        'product_categories',
        sa.Column('product_categories_id', sa.Integer(), nullable=False),
        sa.Column('product_categories_name', sa.String(length=128), nullable=False),
        sa.Column('create_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('product_categories_id'),
    )


def downgrade():
    op.drop_table('product_categories')
