"""create shop_user（含個人資料／行銷偏好欄位，與 e8 擴充後一致）

Revision ID: a3c1d9f4b210
Revises:
Create Date: 2026-03-18

說明：此檔為 user 表初次建立；個人資料／行銷相關欄位已合併於此，與 app.models.User 一致。
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'a3c1d9f4b210'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user',
        sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_name', sa.String(length=32), nullable=False),
        sa.Column('phone_number', sa.String(length=8), nullable=True),
        sa.Column('mail', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=True),
        sa.Column('create_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('salutation', sa.String(length=32), nullable=True),
        sa.Column('birthday', sa.Date(), nullable=True),
        sa.Column('nationality', sa.String(length=64), nullable=True),
        sa.Column(
            'communication_language',
            sa.String(length=32),
            nullable=True,
            server_default=sa.text("'繁體'"),
        ),
        sa.Column(
            'marketing_opt_out',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
        ),
        sa.Column(
            'brand_fortress',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('true'),
        ),
        sa.Column(
            'brand_parknshop',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('true'),
        ),
        sa.Column(
            'brand_watsons',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('true'),
        ),
        sa.Column(
            'brand_moneyback',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('true'),
        ),
        sa.PrimaryKeyConstraint('user_uuid'),
        sa.UniqueConstraint('mail', name='uq_user_mail'),
    )
    op.create_index('ix_user_user_name', 'user', ['user_name'], unique=False)
    op.create_index('ix_user_phone_number', 'user', ['phone_number'], unique=False)


def downgrade():
    op.drop_index('ix_user_phone_number', table_name='user')
    op.drop_index('ix_user_user_name', table_name='user')
    op.drop_table('user')
