"""Changes the guest makes by hand on the Preferences page (ADR 0026).

They go through the same `Operation` validation and `apply_operations` as the
chat's extraction, so both paths store, replace and remove facts the same way.
"""

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.operations import Operation
from app.memory.preference import Preference
from app.memory.profile import PreferenceOut, preference_history
from app.memory.supersede import apply_operations
from app.memory.vocabulary import Kind, Status
from app.users.service import lock_user


class InvalidPreference(Exception):
    """The value does not fit its kind (e.g. a budget of 0, or "funday: fish")."""


class PreferenceNotFound(Exception):
    """No active fact with this id belongs to this user."""


async def add_preference(
    session: AsyncSession, user_id: int, kind: Kind, value: str
) -> list[PreferenceOut]:
    """A new fact; a single-valued kind (diet, budget, spice, calories) replaces the old one."""
    await lock_user(session, user_id)
    await apply_operations(session, user_id, [_operation("add", kind, value)], None)
    return await preference_history(session, user_id)


async def change_preference(
    session: AsyncSession, user_id: int, pref_id: int, value: str
) -> list[PreferenceOut]:
    """Replace one fact with a new value of the same kind; the old row stays as history."""
    await lock_user(session, user_id)
    row = await _owned_active(session, user_id, pref_id)
    op = _operation("supersede", Kind(row.kind), value, row.id)
    await apply_operations(session, user_id, [op], None)
    return await preference_history(session, user_id)


async def remove_preference(
    session: AsyncSession, user_id: int, pref_id: int
) -> list[PreferenceOut]:
    await lock_user(session, user_id)
    row = await _owned_active(session, user_id, pref_id)
    op = _operation("remove", Kind(row.kind), row.value, row.id)
    await apply_operations(session, user_id, [op], None)
    return await preference_history(session, user_id)


def _operation(action: str, kind: Kind, value: str, target_id: int | None = None) -> Operation:
    raw = {"op": action, "kind": kind, "value": value, "target_id": target_id}
    try:
        return Operation.model_validate(raw)
    except ValidationError as exc:
        message = str(exc.errors()[0]["msg"]).removeprefix("Value error, ")
        raise InvalidPreference(message) from exc


async def _owned_active(session: AsyncSession, user_id: int, pref_id: int) -> Preference:
    stmt = select(Preference).where(
        Preference.id == pref_id,
        Preference.user_id == user_id,
        Preference.status == Status.ACTIVE,
    )
    row = await session.scalar(stmt)
    if row is None:
        raise PreferenceNotFound
    return row
