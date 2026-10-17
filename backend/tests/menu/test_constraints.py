"""The database itself rejects menu rows that break the vocabulary or ranges."""

from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.menu.models import MenuItem, Option, OptionGroup
from app.menu.restaurant import Restaurant


async def corner_table(session: AsyncSession) -> int:
    """The migration creates Corner Table, so it exists before any seed."""
    return (
        await session.scalars(select(Restaurant.id).where(Restaurant.slug == "corner-table"))
    ).one()


def dish(restaurant_id: int, **override: object) -> MenuItem:
    item = MenuItem(
        restaurant_id=restaurant_id,
        name="Test Dish",
        category="starters",
        description="A dish used only in tests.",
        price_sar=Decimal("10.00"),
        is_vegetarian=True,
        is_vegan=False,
        spice_level=0,
        ingredients=["water"],
        allergens=[],
        may_contain=[],
        removable=[],
    )
    for field, value in override.items():
        setattr(item, field, value)
    return item


async def with_group(session: AsyncSession, **override: object) -> OptionGroup:
    item = dish(await corner_table(session))
    session.add(item)
    await session.flush()
    group = OptionGroup(item_id=item.id, name="Milk", min_choices=1, max_choices=1, position=0)
    for field, value in override.items():
        setattr(group, field, value)
    return group


def option(group_id: int, **override: object) -> Option:
    row = Option(
        group_id=group_id,
        name="Oat",
        price_delta_sar=Decimal("3.00"),
        allergens=[],
        may_contain=[],
        is_vegetarian=True,
        is_vegan=True,
        spice_level=0,
        position=0,
    )
    for field, value in override.items():
        setattr(row, field, value)
    return row


async def rejected(session: AsyncSession, row: Base) -> None:
    session.add(row)
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_valid_rows_are_accepted(session: AsyncSession) -> None:
    group = await with_group(session)
    session.add(group)
    await session.flush()
    session.add(option(group.id))
    await session.flush()


@pytest.mark.parametrize(
    "override",
    [
        {"allergens": ["lactose"]},
        {"may_contain": ["nuts"]},
        {"spice_level": 4},
        {"price_sar": Decimal("0")},
        {"is_vegan": True, "is_vegetarian": False},
        {"removable": ["salt"]},
    ],
)
async def test_invalid_item_is_rejected(session: AsyncSession, override: dict[str, object]) -> None:
    await rejected(session, dish(await corner_table(session), **override))


async def test_names_are_unique_per_restaurant(session: AsyncSession) -> None:
    rid = await corner_table(session)
    session.add(dish(rid))
    await session.flush()
    await rejected(session, dish(rid))


@pytest.mark.parametrize("override", [{"min_choices": 2, "max_choices": 1}, {"max_choices": 0}])
async def test_invalid_group_is_rejected(
    session: AsyncSession, override: dict[str, object]
) -> None:
    await rejected(session, await with_group(session, **override))


@pytest.mark.parametrize(
    "override",
    [
        {"allergens": ["lactose"]},
        {"price_delta_sar": Decimal("-1")},
        {"spice_level": 4},
        {"is_vegan": True, "is_vegetarian": False},
    ],
)
async def test_invalid_option_is_rejected(
    session: AsyncSession, override: dict[str, object]
) -> None:
    group = await with_group(session)
    session.add(group)
    await session.flush()
    await rejected(session, option(group.id, **override))


@pytest.mark.parametrize(
    "override", [{"slug": "Bad Slug"}, {"accent_color": "purple"}, {"categories": []}]
)
async def test_invalid_restaurant_is_rejected(
    session: AsyncSession, override: dict[str, object]
) -> None:
    fields: dict[str, object] = {
        "slug": "test-place",
        "name": "Test Place",
        "cuisine": "Test",
        "tagline": "Test.",
        "accent_color": "#123456",
        "categories": ["starters"],
        "position": 9,
    }
    await rejected(session, Restaurant(**(fields | override)))
