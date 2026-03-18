"""create shop_user_address

Revision ID: f6b2a0c81d7e
Revises: a3c1d9f4b210
Create Date: 2026-03-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'f6b2a0c81d7e'
down_revision = 'a3c1d9f4b210'
branch_labels = None
depends_on = None


def upgrade():
    # 创建用户收货地址表：一位用户可以有多条地址记录
    op.create_table(
        'user_address',
        # 主键：地址记录唯一识别符（UUID）
        sa.Column('user_address_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        # 外键：所属用户
        sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        # 详细地址文本
        sa.Column('user_address', sa.Text(), nullable=False),
        # 收货电话（可选）
        sa.Column('phone_number', sa.String(length=32), nullable=True),
        # 创建时间：数据库端默认 now()
        sa.Column('create_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        # user_uuid -> user.user_uuid（删除用户时级联删除地址）
        sa.ForeignKeyConstraint(['user_uuid'], ['user.user_uuid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_address_uuid'),
    )
    # 常用查询：按 user_uuid 查该用户所有地址
    op.create_index('ix_user_address_user_uuid', 'user_address', ['user_uuid'], unique=False)


def downgrade():
    # 回滚：先删索引，再删表
    op.drop_index('ix_user_address_user_uuid', table_name='user_address')
    op.drop_table('user_address')
