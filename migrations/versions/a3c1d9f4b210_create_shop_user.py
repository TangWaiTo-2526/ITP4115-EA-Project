"""create shop_user

Revision ID: a3c1d9f4b210
Revises: 6092228cc420
Create Date: 2026-03-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'a3c1d9f4b210'
down_revision = '6092228cc420'
branch_labels = None
depends_on = None


def upgrade():
    # 创建用户表：存放用户基础信息（UUID 主键、邮箱唯一）
    op.create_table(
        'user',
        # 主键：用户唯一识别符（UUID）
        sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        # 用户名（显示用）
        sa.Column('user_name', sa.String(length=32), nullable=False),
        # 电话号码（可选）
        sa.Column('phone_number', sa.String(length=8), nullable=True),
        # 邮箱（用于登录/联系，必须唯一）
        sa.Column('mail', sa.String(length=100), nullable=False),
        # 创建时间：数据库端默认 now()
        sa.Column('create_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('user_uuid'),
        sa.UniqueConstraint('mail', name='uq_user_mail'),
    )
    # 常用查询字段加索引：按用户名/电话检索更快
    op.create_index('ix_user_user_name', 'user', ['user_name'], unique=False)
    op.create_index('ix_user_phone_number', 'user', ['phone_number'], unique=False)


def downgrade():
    # 回滚：先删索引，再删表（顺序与 upgrade 相反）
    op.drop_index('ix_user_phone_number', table_name='user')
    op.drop_index('ix_user_user_name', table_name='user')
    op.drop_table('user')
