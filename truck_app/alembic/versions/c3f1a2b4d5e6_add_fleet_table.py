"""add_fleet_table

Revision ID: c3f1a2b4d5e6
Revises: 0bb131b95781
Create Date: 2026-05-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'c3f1a2b4d5e6'
down_revision: Union[str, Sequence[str], None] = '0bb131b95781'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    vehicletype = postgresql.ENUM(
        'Tractor', '20ft Container', '40ft Container', 'Flatbed', 'Trailer',
        name='vehicletype',
    )
    vehicletype.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'FLEET',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_kyc_id', sa.Integer(), nullable=False),
        sa.Column('vehicle_type', postgresql.ENUM(
            'Tractor', '20ft Container', '40ft Container', 'Flatbed', 'Trailer',
            name='vehicletype', create_type=False,
        ), nullable=False),
        sa.Column('registration_number', sa.String(length=20), nullable=False),
        sa.Column('engine_number', sa.String(length=50), nullable=False),
        sa.Column('chassis_number', sa.String(length=50), nullable=False),
        sa.Column('rc_book_url', sa.String(length=500), nullable=True),
        sa.Column('insurance_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['owner_kyc_id'], ['OWNER_KYC.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('registration_number'),
    )
    op.create_index(op.f('ix_FLEET_id'), 'FLEET', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_FLEET_id'), table_name='FLEET')
    op.drop_table('FLEET')
    op.execute("DROP TYPE IF EXISTS vehicletype")
