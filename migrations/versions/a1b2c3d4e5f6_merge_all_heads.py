"""merge parallel migration branches into single head

Revision ID: a1b2c3d4e5f6
Revises: f3e4d5c6b7a8, e7f8a9b0c123, e2d3c4b5a6f7, f3a4b5c6d7e8
Create Date: 2026-03-22

從 membership (c9d4e27b1aa1) 分出多條分支（訂單、購物車、商品、註冊驗證碼），
合併為單一 head，使 `flask db upgrade` 可一次套用全部遷移。
"""
revision = 'a1b2c3d4e5f6'
down_revision = (
    'f3e4d5c6b7a8',
    'e7f8a9b0c123',
    'e2d3c4b5a6f7',
    'f3a4b5c6d7e8',
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
