"""Alembic does not diff CHECK constraints, so compare the live ones to the enums."""

import re

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.allergens import Allergen
from app.menu.categories import Category

ALLERGENS = {a.value for a in Allergen}
CATEGORIES = {c.value for c in Category}


async def check_values(session: AsyncSession, name: str) -> set[str]:
    sql = text(
        "select pg_get_constraintdef(oid) from pg_constraint "
        "where conrelid = 'menu_items'::regclass and conname = :name"
    )
    definition = (await session.execute(sql, {"name": name})).scalar_one()
    return set(re.findall(r"'([a-z_]+)'", definition))


@pytest.mark.parametrize(
    ("constraint", "expected"),
    [
        ("known_allergens", ALLERGENS),
        ("known_may_contain", ALLERGENS),
        ("known_category", CATEGORIES),
    ],
)
async def test_db_check_matches_enum(
    session: AsyncSession, constraint: str, expected: set[str]
) -> None:
    assert await check_values(session, constraint) == expected
