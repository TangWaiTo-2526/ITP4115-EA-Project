"""add delivery, payment_log, refund, evaluate tables

Revision ID: 6006e1fc6aad
Revises: d1f2e3c4b5a6
Create Date: 2026-03-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '6006e1fc6aad'
down_revision = 'd1f2e3c4b5a6'
branch_labels = None
depends_on = None


def upgrade():
    # 商品配送表格(delivery)
    op.create_table(
        'delivery',
        sa.Column('delivery_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('deliver_time', sa.DateTime(), nullable=True),
        sa.Column('create_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_uuid'], ['user.user_uuid'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_uuid'], ['orders.order_uuid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('delivery_uuid'),
    )
    op.create_index('ix_delivery_user_uuid', 'delivery', ['user_uuid'], unique=False)
    op.create_index('ix_delivery_order_uuid', 'delivery', ['order_uuid'], unique=False)
    op.create_index('ix_delivery_create_time', 'delivery', ['create_time'], unique=False)

    # 支付日誌(payment_log)
    op.create_table(
        'payment_log',
        sa.Column('payment_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payment_methods', sa.String(length=64), nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('state', sa.String(length=64), nullable=False),
        sa.Column('create_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_uuid'], ['user.user_uuid'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_uuid'], ['orders.order_uuid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('payment_uuid'),
    )
    op.create_index('ix_payment_log_user_uuid', 'payment_log', ['user_uuid'], unique=False)
    op.create_index('ix_payment_log_order_uuid', 'payment_log', ['order_uuid'], unique=False)
    op.create_index('ix_payment_log_create_time', 'payment_log', ['create_time'], unique=False)

    # 售後/退款表格(refund)
    op.create_table(
        'refund',
        sa.Column('refund_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('create_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_uuid'], ['user.user_uuid'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_uuid'], ['orders.order_uuid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('refund_uuid'),
    )
    op.create_index('ix_refund_user_uuid', 'refund', ['user_uuid'], unique=False)
    op.create_index('ix_refund_order_uuid', 'refund', ['order_uuid'], unique=False)
    op.create_index('ix_refund_create_time', 'refund', ['create_time'], unique=False)

    # 商品用後評價(evaluate)
    op.create_table(
        'evaluate',
        sa.Column('evaluate_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_details_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('evaluate_txt', sa.Text(), nullable=True),
        sa.Column('create_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_uuid'], ['user.user_uuid'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_details_uuid'], ['product_details.product_categories_uuid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('evaluate_uuid'),
    )
    op.create_index('ix_evaluate_user_uuid', 'evaluate', ['user_uuid'], unique=False)
    op.create_index('ix_evaluate_product_details_uuid', 'evaluate', ['product_details_uuid'], unique=False)
    op.create_index('ix_evaluate_create_time', 'evaluate', ['create_time'], unique=False)


def downgrade():
    op.drop_index('ix_evaluate_create_time', table_name='evaluate')
    op.drop_index('ix_evaluate_product_details_uuid', table_name='evaluate')
    op.drop_index('ix_evaluate_user_uuid', table_name='evaluate')
    op.drop_table('evaluate')

    op.drop_index('ix_refund_create_time', table_name='refund')
    op.drop_index('ix_refund_order_uuid', table_name='refund')
    op.drop_index('ix_refund_user_uuid', table_name='refund')
    op.drop_table('refund')

    op.drop_index('ix_payment_log_create_time', table_name='payment_log')
    op.drop_index('ix_payment_log_order_uuid', table_name='payment_log')
    op.drop_index('ix_payment_log_user_uuid', table_name='payment_log')
    op.drop_table('payment_log')

    op.drop_index('ix_delivery_create_time', table_name='delivery')
    op.drop_index('ix_delivery_order_uuid', table_name='delivery')
    op.drop_index('ix_delivery_user_uuid', table_name='delivery')
    op.drop_table('delivery')