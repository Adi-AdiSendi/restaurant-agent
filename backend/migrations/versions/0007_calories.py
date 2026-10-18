"""Estimated calories: per dish, per option, and snapshotted on order lines.

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-18 12:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0007'
down_revision: Union[str, Sequence[str], None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('menu_items', sa.Column('kcal', sa.Integer(), nullable=True))
    op.add_column(
        'options', sa.Column('kcal_delta', sa.Integer(), server_default=sa.text('0'), nullable=False)
    )
    op.add_column('order_lines', sa.Column('kcal', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('order_lines', 'kcal')
    op.drop_column('options', 'kcal_delta')
    op.drop_column('menu_items', 'kcal')
