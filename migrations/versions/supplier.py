"""create supplier

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-03-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2f3a4b5c6d7'
down_revision = 'd1e2f3a4b5c6'
branch_labels = None
depends_on = None


def upgrade():
    # 创建供应商表：供应商 ID/名称/图片/创建时间
    op.create_table(
        'supplier',
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('supplier_name', sa.String(length=128), nullable=False),
        sa.Column('supplier_png', sa.String(length=256), nullable=True),
        sa.Column('create_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('supplier_id'),
    )


def downgrade():
    op.drop_table('supplier')
