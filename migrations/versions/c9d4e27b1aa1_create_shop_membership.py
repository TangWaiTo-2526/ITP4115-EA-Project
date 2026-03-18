"""create shop_membership

Revision ID: c9d4e27b1aa1
Revises: f6b2a0c81d7e
Create Date: 2026-03-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'c9d4e27b1aa1'
down_revision = 'f6b2a0c81d7e'
branch_labels = None
depends_on = None


def upgrade():
    # 创建会员积分表：每个用户对应一条积分记录（user_uuid 同时是 PK 与 FK）
    op.create_table(
        'membership',
        # 主键 + 外键：直接使用 user_uuid 对应用户（实现 1:1）
        sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        # 会员积分：默认 0
        sa.Column('membership_point', sa.Integer(), nullable=False, server_default='0'),
        # 创建时间：数据库端默认 now()
        sa.Column('create_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        # user_uuid -> user.user_uuid（删除用户时级联删除积分记录）
        sa.ForeignKeyConstraint(['user_uuid'], ['user.user_uuid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_uuid'),
    )


def downgrade():
    # 回滚：删除 membership 表
    op.drop_table('membership')

