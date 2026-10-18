"""Allow day rules and a daily calorie goal as soft preferences.

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-18 12:00:00

"""
from typing import Sequence, Union

from alembic import op

# Copied from app/memory/vocabulary.py on 2026-10-18; a migration must not change later.
DAY_DISLIKE_PATTERN = '^(monday|tuesday|wednesday|thursday|friday|saturday|sunday): [a-z][a-z ,-]{0,48}$'
CALORIES_PATTERN = '^([89][0-9]{2}|[1-5][0-9]{3}|6000)$'

revision: str = '0006'
down_revision: Union[str, Sequence[str], None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_KINDS = "('allergy', 'diet', 'dislike', 'like', 'budget', 'spice')"
NEW_KINDS = "('allergy', 'diet', 'dislike', 'like', 'budget', 'spice', 'day_dislike', 'calories')"
SINGLE_OLD = "('budget', 'diet', 'spice')"
SINGLE_NEW = "('budget', 'calories', 'diet', 'spice')"


def _single_index(kinds: str) -> None:
    op.drop_index('one_active_single_valued', table_name='preferences')
    op.create_index(
        'one_active_single_valued', 'preferences', ['user_id', 'kind'], unique=True,
        postgresql_where=f"status = 'active' AND kind IN {kinds}",
    )


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('pref_kind', 'preferences', type_='check')
    op.create_check_constraint('pref_kind', 'preferences', f'kind IN {NEW_KINDS}')
    op.create_check_constraint(
        'pref_day_format', 'preferences', f"kind <> 'day_dislike' OR value ~ '{DAY_DISLIKE_PATTERN}'"
    )
    op.create_check_constraint(
        'pref_calories', 'preferences', f"kind <> 'calories' OR value ~ '{CALORIES_PATTERN}'"
    )
    _single_index(SINGLE_NEW)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM preferences WHERE kind IN ('day_dislike', 'calories')")
    _single_index(SINGLE_OLD)
    op.drop_constraint('pref_calories', 'preferences', type_='check')
    op.drop_constraint('pref_day_format', 'preferences', type_='check')
    op.drop_constraint('pref_kind', 'preferences', type_='check')
    op.create_check_constraint('pref_kind', 'preferences', f'kind IN {OLD_KINDS}')
