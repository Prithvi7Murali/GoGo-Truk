"""add_company_kyc_table

Revision ID: 3edaa73deca3
Revises: 78b7c8d586a9
Create Date: 2026-05-09 15:03:09.835149

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '3edaa73deca3'
down_revision: Union[str, Sequence[str], None] = '78b7c8d586a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# kycstatus already exists in the DB (created by create_all in Story 1)
kycstatus   = postgresql.ENUM('PENDING', 'VERIFIED', 'REJECTED', name='kycstatus', create_type=False)
companytype = postgresql.ENUM('PVT_LTD', 'LLP', 'PARTNERSHIP', 'LIMITED', name='companytype', create_type=False)


def upgrade() -> None:
    companytype.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'COMPANY_KYC',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('company_type', companytype, nullable=False),
        sa.Column('gst_number', sa.String(length=15), nullable=False),
        sa.Column('registered_address_1', sa.String(length=255), nullable=False),
        sa.Column('registered_address_2', sa.String(length=255), nullable=True),
        sa.Column('registered_address_3', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('pincode', sa.String(length=6), nullable=False),
        sa.Column('contact_person_name', sa.String(length=200), nullable=False),
        sa.Column('contact_person_mobile', sa.String(length=15), nullable=False),
        sa.Column('contact_person_email', sa.String(length=255), nullable=False),
        sa.Column('incorporation_cert_url', sa.String(length=500), nullable=True),
        sa.Column('gst_certificate_url', sa.String(length=500), nullable=True),
        sa.Column('status', kycstatus, nullable=True),
        sa.Column('customer_kyc_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_kyc_id'], ['CUSTOMER_KYC.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('gst_number'),
    )
    op.create_index(op.f('ix_COMPANY_KYC_id'), 'COMPANY_KYC', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_COMPANY_KYC_id'), table_name='COMPANY_KYC')
    op.drop_table('COMPANY_KYC')
    companytype.drop(op.get_bind(), checkfirst=True)
