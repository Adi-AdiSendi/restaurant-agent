"""Edits by hand go through the chat's validation and supersession (ADR 0026)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.manual_edit import (
    InvalidPreference,
    PreferenceNotFound,
    add_preference,
    change_preference,
    remove_preference,
)
from app.memory.profile import PreferenceOut
from app.memory.vocabulary import Kind
from tests.conftest import make_user


def active(history: list[PreferenceOut]) -> list[tuple[str, str]]:
    return sorted((p.kind, p.value) for p in history if p.status == "active")


def row(history: list[PreferenceOut], kind: str) -> PreferenceOut:
    return next(p for p in history if p.kind == kind and p.status == "active")


async def test_add_normalises_like_the_chat(session: AsyncSession) -> None:
    user = await make_user(session, "hand_add")
    history = await add_preference(session, user, Kind.DAY_LIKE, "Fridays: Fish")
    assert active(history) == [("day_like", "friday: fish")]
    assert history[0].is_hard is False


async def test_a_single_valued_kind_replaces_the_old_value(session: AsyncSession) -> None:
    user = await make_user(session, "hand_spice")
    await add_preference(session, user, Kind.SPICE, "mild")
    history = await add_preference(session, user, Kind.SPICE, "hot")
    assert active(history) == [("spice", "hot")]
    old = next(p for p in history if p.value == "mild")
    assert old.status == "superseded" and old.superseded_by == row(history, "spice").id


async def test_change_keeps_the_kind_and_the_old_row_as_history(session: AsyncSession) -> None:
    user = await make_user(session, "hand_change")
    history = await add_preference(session, user, Kind.DISLIKE, "pickles")
    history = await change_preference(session, user, row(history, "dislike").id, "olives")
    assert active(history) == [("dislike", "olives")]
    assert [p.status for p in history if p.value == "pickles"] == ["superseded"]


async def test_remove_ends_a_fact_even_a_hard_one(session: AsyncSession) -> None:
    user = await make_user(session, "hand_remove")
    history = await add_preference(session, user, Kind.ALLERGY, "peanut")
    history = await remove_preference(session, user, row(history, "allergy").id)
    assert active(history) == [] and history[0].status == "removed"


async def test_another_users_or_an_old_fact_is_not_found(session: AsyncSession) -> None:
    alice, bob = await make_user(session, "hand_alice"), await make_user(session, "hand_bob")
    history = await add_preference(session, alice, Kind.ALLERGY, "sesame")
    sesame = row(history, "allergy").id
    with pytest.raises(PreferenceNotFound):
        await remove_preference(session, bob, sesame)
    with pytest.raises(PreferenceNotFound):
        await change_preference(session, bob, sesame, "fish")
    await remove_preference(session, alice, sesame)
    with pytest.raises(PreferenceNotFound):
        await remove_preference(session, alice, sesame)
    with pytest.raises(PreferenceNotFound):
        await remove_preference(session, alice, 999_999)


@pytest.mark.parametrize(
    ("kind", "value", "message"),
    [
        (Kind.BUDGET, "0", "budget must be between"),
        (Kind.CALORIES, "500", "from 800 to 6000 kcal"),
        (Kind.DAY_DISLIKE, "funday: fish", "a day rule must be"),
        (Kind.ALLERGY, "kiwi", "allergy value must be one of"),
    ],
)
async def test_a_bad_value_is_refused_with_a_readable_reason(
    session: AsyncSession, kind: Kind, value: str, message: str
) -> None:
    user = await make_user(session, f"hand_bad_{kind}")
    with pytest.raises(InvalidPreference, match=message):
        await add_preference(session, user, kind, value)


async def test_a_bad_new_value_leaves_the_old_fact(session: AsyncSession) -> None:
    user = await make_user(session, "hand_bad_change")
    history = await add_preference(session, user, Kind.CALORIES, "1800")
    with pytest.raises(InvalidPreference):
        await change_preference(session, user, row(history, "calories").id, "100")
    history = await add_preference(session, user, Kind.LIKE, "salmon")
    assert active(history) == [("calories", "1800"), ("like", "salmon")]
