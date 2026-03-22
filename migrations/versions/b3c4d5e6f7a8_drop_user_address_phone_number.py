"""drop redundant phone_number from user_address (use user.phone_number)

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-03-22

收貨電話與帳戶電話重複時，只保留 user.phone_number。
"""
from alembic import op
import sqlalchemy as sa


revision = 'b3c4d5e6f7a8'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('user_address', 'phone_number')


def downgrade():
    op.add_column(
        'user_address',
        sa.Column('phone_number', sa.String(length=32), nullable=True),
    )
