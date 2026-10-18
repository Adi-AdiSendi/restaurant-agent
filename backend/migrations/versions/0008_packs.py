"""Dishes sold in packs: pieces per pack and what a piece is called.

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-18 14:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0008'
down_revision: Union[str, Sequence[str], None] = '0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'menu_items', sa.Column('pack_size', sa.Integer(), server_default=sa.text('1'), nullable=False)
    )
    op.add_column('menu_items', sa.Column('pack_unit', sa.String(length=20), nullable=True))
    op.create_check_constraint('pack_size_range', 'menu_items', 'pack_size BETWEEN 1 AND 24')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('pack_size_range', 'menu_items', type_='check')
    op.drop_column('menu_items', 'pack_unit')
    op.drop_column('menu_items', 'pack_size')
