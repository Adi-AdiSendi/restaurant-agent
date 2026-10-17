"""Add carts and orders (ADR 0019).

Cart lines keep IDs and removals only; order lines are a snapshot of names,
prices, options, removals and allergens at checkout.

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-17 21:22:10.025671

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0004'
down_revision: Union[str, Sequence[str], None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('carts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('restaurant_id', sa.Integer(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_table('orders',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('restaurant_id', sa.Integer(), nullable=False),
    sa.Column('fulfilment', sa.String(length=10), nullable=False),
    sa.Column('total_sar', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('placed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("fulfilment IN ('pickup', 'dine_in')", name='known_fulfilment'),
    sa.CheckConstraint('total_sar > 0', name='total_positive'),
    sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_user_id'), 'orders', ['user_id'], unique=False)
    op.create_table('cart_lines',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cart_id', sa.Integer(), nullable=False),
    sa.Column('item_id', sa.Integer(), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('option_ids', postgresql.ARRAY(sa.Integer()), nullable=False),
    sa.Column('removed', postgresql.ARRAY(sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('quantity BETWEEN 1 AND 20', name='cart_quantity_range'),
    sa.ForeignKeyConstraint(['cart_id'], ['carts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['item_id'], ['menu_items.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cart_lines_cart_id'), 'cart_lines', ['cart_id'], unique=False)
    op.create_table('order_lines',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('item_id', sa.Integer(), nullable=True),
    sa.Column('item_name', sa.String(length=80), nullable=False),
    sa.Column('category', sa.String(length=40), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('unit_price_sar', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.Column('option_names', postgresql.ARRAY(sa.Text()), nullable=False),
    sa.Column('removed', postgresql.ARRAY(sa.Text()), nullable=False),
    sa.Column('allergens', postgresql.ARRAY(sa.Text()), nullable=False),
    sa.CheckConstraint('quantity BETWEEN 1 AND 20', name='order_quantity_range'),
    sa.ForeignKeyConstraint(['item_id'], ['menu_items.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_order_lines_order_id'), 'order_lines', ['order_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_order_lines_order_id'), table_name='order_lines')
    op.drop_table('order_lines')
    op.drop_index(op.f('ix_cart_lines_cart_id'), table_name='cart_lines')
    op.drop_table('cart_lines')
    op.drop_index(op.f('ix_orders_user_id'), table_name='orders')
    op.drop_table('orders')
    op.drop_table('carts')
