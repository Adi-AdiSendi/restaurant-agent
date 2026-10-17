"""Every branch of apply_operations. These carry the evolving-preferences guarantee."""

import logging

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.operations import Operation
from app.memory.preference import Preference
from app.memory.supersede import apply_operations
from tests.conftest import make_user


def add(kind: str, value: str) -> Operation:
    return Operation.model_validate({"op": "add", "kind": kind, "value": value})


def change(action: str, target: int, kind: str = "diet", value: str = "vegan") -> Operation:
    return Operation.model_validate(
        {"op": action, "kind": kind, "value": value, "target_id": target}
    )


async def rows(session: AsyncSession, user_id: int) -> list[tuple[str, str, str]]:
    stmt = select(Preference).where(Preference.user_id == user_id).order_by(Preference.id)
    return [(p.kind, p.value, p.status) for p in await session.scalars(stmt)]


async def only(session: AsyncSession, user_id: int) -> Preference:
    stmt = select(Preference).where(Preference.user_id == user_id, Preference.status == "active")
    return (await session.scalars(stmt)).one()


async def test_add_stores_a_new_fact(session: AsyncSession) -> None:
    user = await make_user(session, "user1")
    await apply_operations(session, user, [add("allergy", "peanut")], None)
    assert await rows(session, user) == [("allergy", "peanut", "active")]


async def test_adding_the_same_fact_twice_is_a_no_op(session: AsyncSession) -> None:
    user = await make_user(session, "user1")
    await apply_operations(session, user, [add("allergy", "peanut")], None)
    await apply_operations(session, user, [add("allergy", "peanut")], None)
    assert await rows(session, user) == [("allergy", "peanut", "active")]


async def test_many_allergies_can_be_active(session: AsyncSession) -> None:
    user = await make_user(session, "user1")
    await apply_operations(session, user, [add("allergy", "peanut"), add("allergy", "dairy")], None)
    assert [r[2] for r in await rows(session, user)] == ["active", "active"]


async def test_new_single_valued_fact_supersedes_the_old_one(session: AsyncSession) -> None:
    user = await make_user(session, "user1")
    await apply_operations(session, user, [add("budget", "40")], None)
    await apply_operations(session, user, [add("budget", "70")], None)
    assert await rows(session, user) == [
        ("budget", "40.00", "superseded"),
        ("budget", "70.00", "active"),
    ]
    old = await session.scalar(select(Preference).where(Preference.value == "40.00"))
    assert old is not None
    assert old.superseded_by == (await only(session, user)).id


async def test_like_replaces_an_opposite_dislike(session: AsyncSession) -> None:
    user = await make_user(session, "user1")
    await apply_operations(session, user, [add("dislike", "mushrooms")], None)
    await apply_operations(session, user, [add("like", "mushrooms")], None)
    assert await rows(session, user) == [
        ("dislike", "mushrooms", "superseded"),
        ("like", "mushrooms", "active"),
    ]


async def test_supersede_replaces_the_target(
    session: AsyncSession, caplog: pytest.LogCaptureFixture
) -> None:
    user = await make_user(session, "user1")
    await apply_operations(session, user, [add("diet", "vegetarian")], None)
    target = await only(session, user)
    with caplog.at_level(logging.INFO, logger="app.memory.supersede"):
        await apply_operations(session, user, [change("supersede", target.id)], None)
    assert await rows(session, user) == [
        ("diet", "vegetarian", "superseded"),
        ("diet", "vegan", "active"),
    ]
    # The target is also the single-valued conflict; it is superseded exactly once.
    assert sum("memory_superseded" in r.message for r in caplog.records) == 1


async def test_remove_retires_the_target(session: AsyncSession) -> None:
    user = await make_user(session, "user1")
    await apply_operations(session, user, [add("diet", "vegetarian")], None)
    target = await only(session, user)
    await apply_operations(session, user, [change("remove", target.id)], None)
    assert await rows(session, user) == [("diet", "vegetarian", "removed")]


async def test_another_users_target_is_never_touched(session: AsyncSession) -> None:
    alice, bob = await make_user(session, "alice"), await make_user(session, "bob")
    await apply_operations(session, alice, [add("allergy", "peanut")], None)
    alice_row = await only(session, alice)
    await apply_operations(
        session, bob, [change("remove", alice_row.id, "allergy", "peanut")], None
    )
    await apply_operations(session, bob, [change("supersede", alice_row.id)], None)
    assert await rows(session, alice) == [("allergy", "peanut", "active")]
    assert await rows(session, bob) == []


async def test_inactive_target_is_dropped(session: AsyncSession) -> None:
    user = await make_user(session, "user1")
    await apply_operations(session, user, [add("diet", "vegetarian")], None)
    target = await only(session, user)
    await apply_operations(session, user, [change("remove", target.id)], None)
    await apply_operations(session, user, [change("supersede", target.id)], None)
    assert await rows(session, user) == [("diet", "vegetarian", "removed")]


async def test_mismatched_target_cannot_delete_an_allergy(session: AsyncSession) -> None:
    """A wrong target_id from extraction must not switch off a hard constraint."""
    user = await make_user(session, "user1")
    await apply_operations(session, user, [add("allergy", "peanut")], None)
    peanut = await only(session, user)
    wrong = [change("remove", peanut.id, "diet", "vegetarian"), change("supersede", peanut.id)]
    await apply_operations(session, user, wrong, None)
    assert await rows(session, user) == [("allergy", "peanut", "active")]
