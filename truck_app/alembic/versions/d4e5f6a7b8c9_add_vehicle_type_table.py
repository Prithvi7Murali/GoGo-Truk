"""add_vehicle_type_table

Revision ID: d4e5f6a7b8c9
Revises: c3f1a2b4d5e6
Create Date: 2026-05-10 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3f1a2b4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'VEHICLE_TYPE',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('max_load_capacity', sa.Float(), nullable=True),
        sa.Column('dimensions', sa.String(length=200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('type_name'),
    )
    op.create_index(op.f('ix_VEHICLE_TYPE_id'), 'VEHICLE_TYPE', ['id'], unique=False)

    # Seed the original 5 vehicle types
    op.execute("""
        INSERT INTO "VEHICLE_TYPE" (type_name, description, is_active) VALUES
        ('Tractor',        'Standard tractor unit for long-haul freight',      true),
        ('20ft Container', '20 foot shipping container truck',                  true),
        ('40ft Container', '40 foot shipping container truck',                  true),
        ('Flatbed',        'Open flatbed truck for oversized or bulk cargo',    true),
        ('Trailer',        'Standard trailer for general freight',              true)
    """)

    # Convert FLEET.vehicle_type from PostgreSQL enum to plain varchar
    op.execute('ALTER TABLE "FLEET" ALTER COLUMN vehicle_type TYPE VARCHAR(100) USING vehicle_type::text')

    # Drop the now-unused vehicletype enum
    op.execute('DROP TYPE IF EXISTS vehicletype')


def downgrade() -> None:
    op.execute("""
        CREATE TYPE vehicletype AS ENUM
        ('Tractor', '20ft Container', '40ft Container', 'Flatbed', 'Trailer')
    """)
    op.execute("""
        ALTER TABLE "FLEET" ALTER COLUMN vehicle_type
        TYPE vehicletype USING vehicle_type::vehicletype
    """)
    op.drop_index(op.f('ix_VEHICLE_TYPE_id'), table_name='VEHICLE_TYPE')
    op.drop_table('VEHICLE_TYPE')
