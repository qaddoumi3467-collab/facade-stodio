"""element designer

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-12 14:02:28.707905
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('elements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('position', sa.String(length=64), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('system_id', sa.Integer(), nullable=False),
    sa.Column('width_mm', sa.Numeric(precision=8, scale=1), nullable=False),
    sa.Column('height_mm', sa.Numeric(precision=8, scale=1), nullable=False),
    sa.Column('frame_profile_id', sa.Integer(), nullable=False),
    sa.Column('mullion_profile_id', sa.Integer(), nullable=True),
    sa.Column('transom_profile_id', sa.Integer(), nullable=True),
    sa.Column('sash_profile_id', sa.Integer(), nullable=True),
    sa.Column('bead_profile_id', sa.Integer(), nullable=True),
    sa.Column('glass_id', sa.Integer(), nullable=False),
    sa.Column('layout', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['bead_profile_id'], ['profiles.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['frame_profile_id'], ['profiles.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['glass_id'], ['glass_types.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['mullion_profile_id'], ['profiles.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['sash_profile_id'], ['profiles.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['system_id'], ['profile_systems.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['transom_profile_id'], ['profiles.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_elements_system_id'), 'elements', ['system_id'], unique=False)
    op.add_column('profile_systems', sa.Column('sash_overlap_mm', sa.Numeric(precision=6, scale=2), server_default='0', nullable=False))
    op.add_column('profile_systems', sa.Column('glass_bite_mm', sa.Numeric(precision=6, scale=2), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('profile_systems', 'glass_bite_mm')
    op.drop_column('profile_systems', 'sash_overlap_mm')
    op.drop_index(op.f('ix_elements_system_id'), table_name='elements')
    op.drop_table('elements')
