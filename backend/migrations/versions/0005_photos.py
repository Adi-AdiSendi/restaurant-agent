"""Add a photo name to menu items and restaurants (ADR 0024).

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-18 09:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0005'
down_revision: Union[str, Sequence[str], None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PHOTO_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*/[a-z0-9]+(-[a-z0-9]+)*$"


def upgrade() -> None:
    """Upgrade schema."""
    for table in ('menu_items', 'restaurants'):
        op.add_column(table, sa.Column('photo', sa.String(length=100), nullable=True))
        op.create_check_constraint('photo_format', table, f"photo ~ '{PHOTO_PATTERN}'")


def downgrade() -> None:
    """Downgrade schema."""
    for table in ('restaurants', 'menu_items'):
        op.drop_constraint('photo_format', table, type_='check')
        op.drop_column(table, 'photo')
