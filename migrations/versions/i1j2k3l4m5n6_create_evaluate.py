"""create evaluate table

Revision ID: i1j2k3l4m5n6
Revises: h0i1j2k3l4m5
Create Date: 2026-04-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'i1j2k3l4m5n6'
down_revision = 'h0i1j2k3l4m5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'evaluate',
        sa.Column('evaluate_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_details_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('evalate_txt', sa.Text(), nullable=True),
        sa.Column('create_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(
            ['product_details_uuid'],
            ['product_details.product_categories_uuid'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(['user_uuid'], ['user.user_uuid'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('evaluate_uuid'),
    )
    op.create_index('ix_evaluate_product_details_uuid', 'evaluate', ['product_details_uuid'], unique=False)
    op.create_index('ix_evaluate_user_uuid', 'evaluate', ['user_uuid'], unique=False)


def downgrade():
    op.drop_index('ix_evaluate_user_uuid', table_name='evaluate')
    op.drop_index('ix_evaluate_product_details_uuid', table_name='evaluate')
    op.drop_table('evaluate')