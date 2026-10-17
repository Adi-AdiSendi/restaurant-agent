"""Create menu_items with data-integrity CHECK constraints.

Revision ID: 0001
Revises: 
Create Date: 2026-10-17 08:58:58.117046

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('menu_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('category', sa.String(length=40), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('price_sar', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('is_vegetarian', sa.Boolean(), nullable=False),
    sa.Column('is_vegan', sa.Boolean(), nullable=False),
    sa.Column('spice_level', sa.Integer(), nullable=False),
    sa.Column('ingredients', postgresql.ARRAY(sa.Text()), nullable=False),
    sa.Column('allergens', postgresql.ARRAY(sa.Text()), nullable=False),
    sa.Column('may_contain', postgresql.ARRAY(sa.Text()), nullable=False),
    sa.CheckConstraint("allergens <@ ARRAY['gluten', 'dairy', 'egg', 'peanut', 'tree_nut', 'soy', 'sesame', 'fish', 'shellfish', 'mustard']::text[]", name='known_allergens'),
    sa.CheckConstraint("category = ANY(ARRAY['starters', 'burgers_and_mains', 'bowls_and_pasta', 'desserts_and_drinks']::text[])", name='known_category'),
    sa.CheckConstraint("may_contain <@ ARRAY['gluten', 'dairy', 'egg', 'peanut', 'tree_nut', 'soy', 'sesame', 'fish', 'shellfish', 'mustard']::text[]", name='known_may_contain'),
    sa.CheckConstraint('NOT is_vegan OR is_vegetarian', name='vegan_is_vegetarian'),
    sa.CheckConstraint('price_sar > 0', name='price_positive'),
    sa.CheckConstraint('spice_level BETWEEN 0 AND 3', name='spice_range'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('menu_items')
