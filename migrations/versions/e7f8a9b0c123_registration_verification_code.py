"""registration_verification_code audit table

Revision ID: e7f8a9b0c123
Revises: c9d4e27b1aa1
Create Date: 2026-03-22

"""
from alembic import op
import sqlalchemy as sa


revision = 'e7f8a9b0c123'
down_revision = 'c9d4e27b1aa1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'registration_verification_code',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_ip', sa.String(length=45), nullable=False),
        sa.Column('code', sa.String(length=6), nullable=False),
        sa.Column('mail', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_sent_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_registration_verification_code_client_ip'),
        'registration_verification_code',
        ['client_ip'],
        unique=False,
    )
    op.create_index(
        op.f('ix_registration_verification_code_mail'),
        'registration_verification_code',
        ['mail'],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f('ix_registration_verification_code_mail'), table_name='registration_verification_code')
    op.drop_index(op.f('ix_registration_verification_code_client_ip'), table_name='registration_verification_code')
    op.drop_table('registration_verification_code')
