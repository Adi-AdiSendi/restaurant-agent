"""Apply memory operations for one user. Old facts are replaced, never stacked.

Every query here is filtered by `user_id`; a target_id owned by someone else
is treated as missing.
"""

import logging
from collections.abc import Sequence

from sqlalchemy import ColumnElement, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.operations import Operation
from app.memory.preference import Preference
from app.memory.vocabulary import OPPOSITE_KINDS, SINGLE_VALUED_KINDS, Status

logger = logging.getLogger(__name__)


async def apply_operations(
    session: AsyncSession, user_id: int, ops: Sequence[Operation], source_message_id: int | None
) -> None:
    for op in ops:
        if op.op == "add":
            await _add(session, user_id, op, source_message_id, replacing=[])
        elif op.op == "supersede":
            target = await _owned_active(session, user_id, op)
            if target is not None:
                await _add(session, user_id, op, source_message_id, replacing=[target])
        else:
            target = await _owned_active(session, user_id, op)
            if target is not None:
                target.status = Status.REMOVED
                logger.info("memory_removed id=%d kind=%s", target.id, target.kind)
    await session.flush()


async def _owned_active(session: AsyncSession, user_id: int, op: Operation) -> Preference | None:
    target = await _first(
        session, user_id, Preference.id == op.target_id, Preference.status == Status.ACTIVE
    )
    if target is None or not op.matches_target(target.kind, target.value):
        logger.warning("memory_target_dropped op=%s target_id=%s", op.op, op.target_id)
        return None
    return target


async def _add(
    session: AsyncSession,
    user_id: int,
    op: Operation,
    source_message_id: int | None,
    replacing: list[Preference],
) -> None:
    """Insert kind=value, marking `replacing` and any conflicting active row superseded."""
    same = await _active(session, user_id, op.kind, op.value)
    if op.kind in SINGLE_VALUED_KINDS:
        conflict = await _active(session, user_id, op.kind)
    elif op.kind in OPPOSITE_KINDS:
        conflict = await _active(session, user_id, OPPOSITE_KINDS[op.kind], op.value)
    else:
        conflict = None
    # The target of a supersede is often also the single-valued conflict: keep it once.
    candidates = {p.id: p for p in [*replacing, conflict] if p is not None and p is not same}
    old = list(candidates.values())
    for row in old:
        row.status = Status.SUPERSEDED
    await session.flush()
    new = same
    if new is None:
        new = Preference(
            user_id=user_id, kind=op.kind, value=op.value, source_message_id=source_message_id
        )
        session.add(new)
        await session.flush()
        logger.info("memory_added id=%d kind=%s", new.id, new.kind)
    for row in old:
        row.superseded_by = new.id
        logger.info("memory_superseded id=%d by=%d", row.id, new.id)


async def _active(
    session: AsyncSession, user_id: int, kind: str, value: str | None = None
) -> Preference | None:
    conditions = [Preference.kind == kind, Preference.status == Status.ACTIVE]
    if value is not None:
        conditions.append(Preference.value == value)
    return await _first(session, user_id, *conditions)


async def _first(
    session: AsyncSession, user_id: int, *conditions: ColumnElement[bool]
) -> Preference | None:
    stmt = select(Preference).where(Preference.user_id == user_id, *conditions)
    return await session.scalar(stmt.limit(1))
