from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.models import MenuItem
from app.menu.schemas import MenuItemOut
from scripts.seed_menu import load_menu, seed_menu


async def count(session: AsyncSession) -> int:
    return (await session.scalar(select(func.count()).select_from(MenuItem))) or 0


async def by_name(session: AsyncSession, name: str) -> MenuItem | None:
    return await session.scalar(select(MenuItem).where(MenuItem.name == name))


async def test_seed_twice_does_not_duplicate(session: AsyncSession) -> None:
    items = load_menu()
    await seed_menu(session, items)
    await seed_menu(session, items)
    assert await count(session) == len(items)


async def test_reseed_updates_changed_fields(session: AsyncSession) -> None:
    items = load_menu()
    await seed_menu(session, items)
    changed = [
        i.model_copy(update={"price_sar": Decimal("25.50")}) if i.name == items[0].name else i
        for i in items
    ]
    await seed_menu(session, changed)
    session.expire_all()
    item = await by_name(session, items[0].name)
    assert item is not None
    assert item.price_sar == Decimal("25.50")


async def test_reseed_deletes_dishes_removed_from_file(session: AsyncSession) -> None:
    items = load_menu()
    await seed_menu(session, items)
    await seed_menu(session, items[1:])
    assert await count(session) == len(items) - 1
    assert await by_name(session, items[0].name) is None


async def test_every_seeded_row_validates_as_output(session: AsyncSession) -> None:
    await seed_menu(session, load_menu())
    rows = (await session.scalars(select(MenuItem))).all()
    assert [MenuItemOut.model_validate(row).name for row in rows]


def test_empty_menu_file_is_rejected(tmp_path: Path) -> None:
    empty = tmp_path / "menu.json"
    empty.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="no menu items"):
        load_menu(empty)
