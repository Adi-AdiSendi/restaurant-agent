from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.models import MenuItem, Option, OptionGroup
from app.menu.restaurant_schemas import RestaurantFile
from app.menu.schemas import MenuItemOut
from scripts.menu_sync import sync_restaurant
from scripts.seed_menu import load_restaurants, seed_menus

CORNER_TABLE = load_restaurants()[0]


def option(name: str, **extra: Any) -> dict[str, Any]:
    base: dict[str, Any] = {"name": name, "price_delta_sar": "0.00", "allergens": []}
    flags: dict[str, Any] = {
        "may_contain": [],
        "is_vegetarian": True,
        "is_vegan": True,
        "spice_level": 0,
    }
    return base | flags | extra


def bistro(*milks: str, item_name: str = "Truffle Parmesan Fries") -> RestaurantFile:
    """A small test restaurant. Its item name deliberately repeats a Corner Table one."""
    groups = [
        {"name": "Milk", "min_choices": 1, "max_choices": 1, "options": [option(m) for m in milks]}
    ]
    item = {
        "name": item_name,
        "category": "drinks",
        "description": "Test.",
        "price_sar": "10.00",
        "is_vegetarian": True,
        "is_vegan": True,
        "spice_level": 0,
        "ingredients": ["coffee"],
        "allergens": [],
        "may_contain": [],
        "option_groups": groups if milks else [],
    }
    return RestaurantFile.model_validate(
        {
            "slug": "test-bistro",
            "name": "Test Bistro",
            "cuisine": "Cafe",
            "tagline": "Test.",
            "accent_color": "#123456",
            "categories": ["drinks"],
            "items": [item],
        }
    )


async def items_of(session: AsyncSession, restaurant_id: int) -> list[MenuItem]:
    stmt = select(MenuItem).where(MenuItem.restaurant_id == restaurant_id).order_by(MenuItem.id)
    return list((await session.scalars(stmt)).all())


async def option_ids(session: AsyncSession, item_id: int) -> dict[str, int]:
    stmt = select(Option.name, Option.id).join(OptionGroup).where(OptionGroup.item_id == item_id)
    return {name: oid for name, oid in (await session.execute(stmt)).all()}


async def test_seed_twice_keeps_ids_and_does_not_duplicate(session: AsyncSession) -> None:
    rid = await sync_restaurant(session, CORNER_TABLE, 0)
    first = [i.id for i in await items_of(session, rid)]
    await sync_restaurant(session, CORNER_TABLE, 0)
    session.expire_all()
    assert [i.id for i in await items_of(session, rid)] == first
    assert len(first) == len(CORNER_TABLE.items)


async def test_reseed_updates_changed_fields(session: AsyncSession) -> None:
    first = CORNER_TABLE.items[0]
    changed = CORNER_TABLE.model_copy(
        update={
            "items": [
                first.model_copy(update={"price_sar": Decimal("25.50")}),
                *CORNER_TABLE.items[1:],
            ]
        }
    )
    rid = await sync_restaurant(session, changed, 0)
    session.expire_all()
    item = next(i for i in await items_of(session, rid) if i.name == first.name)
    assert item.price_sar == Decimal("25.50")


async def test_reseed_deletes_dishes_removed_from_the_file(session: AsyncSession) -> None:
    rid = await sync_restaurant(session, CORNER_TABLE, 0)
    shorter = CORNER_TABLE.model_copy(update={"items": CORNER_TABLE.items[1:]})
    await sync_restaurant(session, shorter, 0)
    names = [i.name for i in await items_of(session, rid)]
    assert CORNER_TABLE.items[0].name not in names
    assert len(names) == len(CORNER_TABLE.items) - 1


async def test_restaurants_do_not_touch_each_other(session: AsyncSession) -> None:
    corner = await sync_restaurant(session, CORNER_TABLE, 0)
    before = [(i.id, i.name, i.price_sar) for i in await items_of(session, corner)]
    other = await sync_restaurant(session, bistro("Whole"), 1)
    await sync_restaurant(session, bistro("Whole", item_name="Flat White"), 1)
    session.expire_all()
    assert [(i.id, i.name, i.price_sar) for i in await items_of(session, corner)] == before
    assert [i.name for i in await items_of(session, other)] == ["Flat White"]


async def test_options_keep_ids_and_removed_ones_are_deleted(session: AsyncSession) -> None:
    rid = await sync_restaurant(session, bistro("Whole", "Oat", "Almond"), 1)
    item_id = (await items_of(session, rid))[0].id
    first = await option_ids(session, item_id)
    await sync_restaurant(session, bistro("Whole", "Oat"), 1)
    assert await option_ids(session, item_id) == {"Whole": first["Whole"], "Oat": first["Oat"]}
    await sync_restaurant(session, bistro(), 1)
    assert await option_ids(session, item_id) == {}
    groups = select(func.count()).select_from(OptionGroup).where(OptionGroup.item_id == item_id)
    assert await session.scalar(groups) == 0


async def test_every_seeded_row_validates_as_output(session: AsyncSession) -> None:
    await seed_menus(session, load_restaurants())
    rows = (await session.scalars(select(MenuItem))).all()
    assert all(MenuItemOut.model_validate(row).name for row in rows)


def test_folder_without_files_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no restaurant files"):
        load_restaurants(tmp_path)


def test_file_name_must_match_slug(tmp_path: Path) -> None:
    (tmp_path / "wrong-name.json").write_text(bistro("Whole").model_dump_json(), encoding="utf-8")
    with pytest.raises(ValueError, match="must match the file name"):
        load_restaurants(tmp_path)
