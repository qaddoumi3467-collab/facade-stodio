"""catalog tables

Revision ID: 0001
Revises:
Create Date: 2026-10-12 13:41:34.967054
"""
from alembic import op
import sqlalchemy as sa


revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('glass_types',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=64), nullable=False),
    sa.Column('name_en', sa.String(length=200), nullable=False),
    sa.Column('name_ar', sa.String(length=200), nullable=False),
    sa.Column('build_up', sa.String(length=100), nullable=True),
    sa.Column('total_thickness_mm', sa.Numeric(precision=6, scale=2), nullable=False),
    sa.Column('glass_thickness_mm', sa.Numeric(precision=6, scale=2), nullable=False),
    sa.Column('u_value', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('price_per_m2', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('profile_systems',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=64), nullable=False),
    sa.Column('name_en', sa.String(length=200), nullable=False),
    sa.Column('name_ar', sa.String(length=200), nullable=False),
    sa.Column('manufacturer', sa.String(length=200), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('thermal_break', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('hardware_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('system_id', sa.Integer(), nullable=True),
    sa.Column('article_no', sa.String(length=64), nullable=False),
    sa.Column('name_en', sa.String(length=200), nullable=False),
    sa.Column('name_ar', sa.String(length=200), nullable=False),
    sa.Column('category', sa.Enum('handle', 'hinge', 'lock', 'gasket', 'corner_cleat', 'roller', 'accessory', 'other', name='hardwarecategory', native_enum=False, length=32), nullable=False),
    sa.Column('unit', sa.Enum('piece', 'set', 'metre', name='hardwareunit', native_enum=False, length=32), nullable=False),
    sa.Column('price_per_unit', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.ForeignKeyConstraint(['system_id'], ['profile_systems.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('article_no')
    )
    op.create_index(op.f('ix_hardware_items_system_id'), 'hardware_items', ['system_id'], unique=False)
    op.create_table('profiles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('system_id', sa.Integer(), nullable=False),
    sa.Column('article_no', sa.String(length=64), nullable=False),
    sa.Column('name_en', sa.String(length=200), nullable=False),
    sa.Column('name_ar', sa.String(length=200), nullable=False),
    sa.Column('role', sa.Enum('frame', 'sash', 'mullion', 'transom', 'glazing_bead', 'threshold', 'coupling', 'other', name='profilerole', native_enum=False, length=32), nullable=False),
    sa.Column('width_mm', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('height_mm', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('weight_kg_per_m', sa.Numeric(precision=8, scale=3), nullable=False),
    sa.Column('bar_length_mm', sa.Integer(), nullable=False),
    sa.Column('price_per_m', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.ForeignKeyConstraint(['system_id'], ['profile_systems.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('article_no')
    )
    op.create_index(op.f('ix_profiles_system_id'), 'profiles', ['system_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_profiles_system_id'), table_name='profiles')
    op.drop_table('profiles')
    op.drop_index(op.f('ix_hardware_items_system_id'), table_name='hardware_items')
    op.drop_table('hardware_items')
    op.drop_table('profile_systems')
    op.drop_table('glass_types')
