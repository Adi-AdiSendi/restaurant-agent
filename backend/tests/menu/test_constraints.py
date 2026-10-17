"""The database itself rejects menu rows that break the vocabulary or ranges."""

from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.models import MenuItem


def dish(**override: object) -> MenuItem:
    item = MenuItem(
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
    )
    for field, value in override.items():
        setattr(item, field, value)
    return item


async def test_valid_row_is_accepted(session: AsyncSession) -> None:
    session.add(dish())
    await session.flush()


@pytest.mark.parametrize(
    "override",
    [
        {"allergens": ["lactose"]},
        {"may_contain": ["nuts"]},
        {"spice_level": 4},
        {"price_sar": Decimal("0")},
        {"category": "mains"},
        {"is_vegan": True, "is_vegetarian": False},
    ],
)
async def test_invalid_row_is_rejected(session: AsyncSession, override: dict[str, object]) -> None:
    session.add(dish(**override))
    with pytest.raises(IntegrityError):
        await session.flush()
