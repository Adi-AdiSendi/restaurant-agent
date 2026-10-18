"""Allow day likes ("friday: fish") as a soft preference.

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-18 18:00:00

"""
from typing import Sequence, Union

from alembic import op

# Copied from app/memory/vocabulary.py on 2026-10-18; a migration must not change later.
DAY_RULE_PATTERN = '^(monday|tuesday|wednesday|thursday|friday|saturday|sunday): [a-z][a-z ,-]{0,48}$'

revision: str = '0009'
down_revision: Union[str, Sequence[str], None] = '0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_KINDS = "('allergy', 'diet', 'dislike', 'like', 'budget', 'spice', 'day_dislike', 'calories')"
NEW_KINDS = (
    "('allergy', 'diet', 'dislike', 'like', 'budget', 'spice', 'day_dislike', 'day_like', "
    "'calories')"
)


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('pref_kind', 'preferences', type_='check')
    op.create_check_constraint('pref_kind', 'preferences', f'kind IN {NEW_KINDS}')
    op.create_check_constraint(
        'pref_day_like_format', 'preferences', f"kind <> 'day_like' OR value ~ '{DAY_RULE_PATTERN}'"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("UPDATE preferences SET superseded_by = NULL WHERE superseded_by IN "
               "(SELECT id FROM preferences WHERE kind = 'day_like')")
    op.execute("DELETE FROM preferences WHERE kind = 'day_like'")
    op.drop_constraint('pref_day_like_format', 'preferences', type_='check')
    op.drop_constraint('pref_kind', 'preferences', type_='check')
    op.create_check_constraint('pref_kind', 'preferences', f'kind IN {OLD_KINDS}')
