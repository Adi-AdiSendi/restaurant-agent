"""Add restaurants, option groups and options; scope items and conversations.

The existing menu and conversations become Corner Table's, so old chats keep
working. Item names become unique per restaurant, and categories are checked
against the restaurant file by the seed instead of a global CHECK.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-17 20:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0003'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ALLERGENS = "ARRAY['gluten', 'dairy', 'egg', 'peanut', 'tree_nut', 'soy', 'sesame', 'fish', 'shellfish', 'mustard']::text[]"
CORNER_TABLE = (
    "INSERT INTO restaurants (slug, name, cuisine, tagline, accent_color, categories, position) "
    "VALUES ('corner-table', 'Corner Table', 'International casual', "
    "'Burgers, bowls, pasta and desserts from around the world.', '#440099', "
    "ARRAY['starters', 'burgers_and_mains', 'bowls_and_pasta', 'desserts_and_drinks'], 0)"
)


def _scope_to_corner_table(table: str) -> None:
    op.add_column(table, sa.Column('restaurant_id', sa.Integer(), nullable=True))
    op.execute(f"UPDATE {table} SET restaurant_id = (SELECT id FROM restaurants WHERE slug = 'corner-table')")
    op.alter_column(table, 'restaurant_id', nullable=False)
    op.create_foreign_key(f'{table}_restaurant_id_fkey', table, 'restaurants', ['restaurant_id'], ['id'], ondelete='RESTRICT')
    op.create_index(op.f(f'ix_{table}_restaurant_id'), table, ['restaurant_id'], unique=False)


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('restaurants',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=40), nullable=False),
    sa.Column('name', sa.String(length=60), nullable=False),
    sa.Column('cuisine', sa.String(length=40), nullable=False),
    sa.Column('tagline', sa.Text(), nullable=False),
    sa.Column('accent_color', sa.String(length=7), nullable=False),
    sa.Column('categories', postgresql.ARRAY(sa.Text()), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.CheckConstraint("slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name='slug_format'),
    sa.CheckConstraint("accent_color ~ '^#[0-9a-f]{6}$'", name='accent_hex'),
    sa.CheckConstraint('cardinality(categories) > 0', name='has_categories'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    sa.UniqueConstraint('slug')
    )
    op.execute(CORNER_TABLE)

    _scope_to_corner_table('menu_items')
    op.drop_constraint('menu_items_name_key', 'menu_items', type_='unique')
    op.create_unique_constraint('menu_items_restaurant_name_key', 'menu_items', ['restaurant_id', 'name'])
    op.drop_constraint('known_category', 'menu_items', type_='check')
    op.add_column('menu_items', sa.Column('removable', postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False))
    op.create_check_constraint('removable_are_ingredients', 'menu_items', 'removable <@ ingredients')
    _scope_to_corner_table('conversations')

    op.create_table('option_groups',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('item_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=60), nullable=False),
    sa.Column('min_choices', sa.Integer(), nullable=False),
    sa.Column('max_choices', sa.Integer(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.CheckConstraint('min_choices >= 0 AND max_choices >= 1', name='choices_positive'),
    sa.CheckConstraint('min_choices <= max_choices', name='min_not_above_max'),
    sa.ForeignKeyConstraint(['item_id'], ['menu_items.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('item_id', 'name', name='option_groups_item_name_key')
    )
    op.create_index(op.f('ix_option_groups_item_id'), 'option_groups', ['item_id'], unique=False)
    op.create_table('options',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=60), nullable=False),
    sa.Column('price_delta_sar', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('allergens', postgresql.ARRAY(sa.Text()), nullable=False),
    sa.Column('may_contain', postgresql.ARRAY(sa.Text()), nullable=False),
    sa.Column('is_vegetarian', sa.Boolean(), nullable=False),
    sa.Column('is_vegan', sa.Boolean(), nullable=False),
    sa.Column('spice_level', sa.Integer(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.CheckConstraint('price_delta_sar >= 0', name='option_price_not_negative'),
    sa.CheckConstraint('spice_level BETWEEN 0 AND 3', name='option_spice_range'),
    sa.CheckConstraint('NOT is_vegan OR is_vegetarian', name='option_vegan_is_vegetarian'),
    sa.CheckConstraint(f'allergens <@ {ALLERGENS}', name='option_known_allergens'),
    sa.CheckConstraint(f'may_contain <@ {ALLERGENS}', name='option_known_may_contain'),
    sa.ForeignKeyConstraint(['group_id'], ['option_groups.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('group_id', 'name', name='options_group_name_key')
    )
    op.create_index(op.f('ix_options_group_id'), 'options', ['group_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema. Other restaurants' items and conversations are deleted."""
    op.drop_index(op.f('ix_options_group_id'), table_name='options')
    op.drop_table('options')
    op.drop_index(op.f('ix_option_groups_item_id'), table_name='option_groups')
    op.drop_table('option_groups')
    corner = "(SELECT id FROM restaurants WHERE slug = 'corner-table')"
    op.execute(f"DELETE FROM conversations WHERE restaurant_id <> {corner}")
    op.execute(f"DELETE FROM menu_items WHERE restaurant_id <> {corner}")
    for table in ('conversations', 'menu_items'):
        op.drop_index(op.f(f'ix_{table}_restaurant_id'), table_name=table)
        op.drop_constraint(f'{table}_restaurant_id_fkey', table, type_='foreignkey')
    op.drop_column('conversations', 'restaurant_id')
    op.drop_constraint('removable_are_ingredients', 'menu_items', type_='check')
    op.drop_column('menu_items', 'removable')
    op.create_check_constraint(
        'known_category', 'menu_items',
        "category = ANY(ARRAY['starters', 'burgers_and_mains', 'bowls_and_pasta', 'desserts_and_drinks']::text[])",
    )
    op.drop_constraint('menu_items_restaurant_name_key', 'menu_items', type_='unique')
    op.create_unique_constraint('menu_items_name_key', 'menu_items', ['name'])
    op.drop_column('menu_items', 'restaurant_id')
    op.drop_table('restaurants')
