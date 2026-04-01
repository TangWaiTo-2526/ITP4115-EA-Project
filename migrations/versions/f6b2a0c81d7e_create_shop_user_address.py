"""create shop_user_address（含送貨細項／電話，與 e8 擴充後一致）

Revision ID: f6b2a0c81d7e
Revises: a3c1d9f4b210
Create Date: 2026-03-18

說明：此檔為 user_address 表初次建立；送貨細項與電話欄位與 app.models.UserAddress 一致。
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'f6b2a0c81d7e'
down_revision = 'a3c1d9f4b210'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_address',
        sa.Column('user_address_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_address', sa.Text(), nullable=False),
        sa.Column('unit', sa.String(length=64), nullable=True),
        sa.Column('floor', sa.String(length=32), nullable=True),
        sa.Column('building_street', sa.String(length=512), nullable=True),
        sa.Column('region', sa.String(length=32), nullable=True),
        sa.Column('district', sa.String(length=64), nullable=True),
        sa.Column('phone_number', sa.String(length=32), nullable=True),
        sa.Column('home_phone', sa.String(length=32), nullable=True),
        sa.Column('create_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_uuid'], ['user.user_uuid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_address_uuid'),
    )
    op.create_index('ix_user_address_user_uuid', 'user_address', ['user_uuid'], unique=False)


def downgrade():
    op.drop_index('ix_user_address_user_uuid', table_name='user_address')
    op.drop_table('user_address')
