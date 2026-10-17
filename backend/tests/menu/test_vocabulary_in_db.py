"""Alembic does not diff CHECK constraints, so compare the live ones to the enum."""

import re

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.allergens import Allergen

ALLERGENS = {a.value for a in Allergen}


async def check_values(session: AsyncSession, table: str, name: str) -> set[str]:
    sql = text(
        "select pg_get_constraintdef(oid) from pg_constraint "
        "where conrelid = cast(:table as regclass) and conname = :name"
    )
    definition = (await session.execute(sql, {"table": table, "name": name})).scalar_one()
    return set(re.findall(r"'([a-z_]+)'", definition))


@pytest.mark.parametrize(
    ("table", "constraint"),
    [
        ("menu_items", "known_allergens"),
        ("menu_items", "known_may_contain"),
        ("options", "option_known_allergens"),
        ("options", "option_known_may_contain"),
    ],
)
async def test_db_check_matches_enum(session: AsyncSession, table: str, constraint: str) -> None:
    assert await check_values(session, table, constraint) == ALLERGENS


async def test_categories_are_not_a_global_check(session: AsyncSession) -> None:
    """Each restaurant lists its own categories; the seed checks items against them."""
    sql = text("select count(*) from pg_constraint where conname = 'known_category'")
    assert (await session.execute(sql)).scalar_one() == 0
