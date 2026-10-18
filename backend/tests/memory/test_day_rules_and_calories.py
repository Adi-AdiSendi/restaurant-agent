from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.prompt import system_prompt
from app.memory.operations import Operation
from app.memory.preference import Preference
from app.memory.supersede import apply_operations
from app.memory.vocabulary import Kind
from app.menu import clock
from app.menu.restaurant import Restaurant
from tests.conftest import make_user


def add(kind: str, value: str) -> Operation:
    return Operation(op="add", kind=Kind(kind), value=value)


@pytest.mark.parametrize(
    ("said", "stored"),
    [
        ("Friday: meat", "friday: meat"),
        ("fridays: Fried food", "friday: fried food"),
        ("on monday: pork", "monday: pork"),
    ],
)
@pytest.mark.parametrize("kind", ["day_dislike", "day_like"])
def test_a_day_rule_is_normalised(kind: str, said: str, stored: str) -> None:
    assert add(kind, said).value == stored


@pytest.mark.parametrize("said", ["meat", "someday: meat", "friday:", "friday: <b>"])
@pytest.mark.parametrize("kind", ["day_dislike", "day_like"])
def test_a_day_rule_needs_a_real_weekday_and_plain_food(kind: str, said: str) -> None:
    with pytest.raises(ValidationError, match="day rule"):
        add(kind, said)


def test_a_calorie_goal_is_a_daily_number_in_range() -> None:
    assert add("calories", "1,800 kcal").value == "1800"
    for bad in ("200", "9000", "lots"):
        with pytest.raises(ValidationError):
            add("calories", bad)


async def test_the_database_refuses_a_malformed_rule_or_goal(session: AsyncSession) -> None:
    user = await make_user(session, "rules_db")
    bad = (("day_dislike", "friday meat"), ("day_like", "fish"), ("calories", "100"))
    for kind, value in bad:
        async with session.begin_nested():
            session.add(Preference(user_id=user, kind=kind, value=value))
            with pytest.raises(IntegrityError):
                await session.flush()


async def test_a_day_like_replaces_the_opposite_day_rule(session: AsyncSession) -> None:
    user = await make_user(session, "rules_flip")
    await apply_operations(session, user, [add("day_dislike", "friday: fish")], None)
    await apply_operations(session, user, [add("day_like", "friday: fish")], None)
    stmt = select(Preference.kind, Preference.status).where(Preference.user_id == user)
    got = sorted((k, s) for k, s in await session.execute(stmt))
    assert got == [("day_dislike", "superseded"), ("day_like", "active")]


def test_riyadh_weekday_and_midnight() -> None:
    late_thursday_utc = datetime(2026, 10, 15, 22, 30, tzinfo=UTC)  # 01:30 Friday in Riyadh
    assert clock.weekday(late_thursday_utc) == "friday"
    assert clock.start_of_day(late_thursday_utc) == datetime(2026, 10, 15, 21, 0, tzinfo=UTC)


def test_the_prompt_names_today_for_day_rules() -> None:
    cafe = Restaurant(
        slug="c",
        name="C",
        cuisine="Cafe",
        tagline="t",
        accent_color="#000000",
        categories=["coffee"],
        position=0,
    )
    prompt = system_prompt(cafe, [], "friday")
    assert "Today is Friday (Riyadh time)" in prompt and "never refuse a dish for it" in prompt
