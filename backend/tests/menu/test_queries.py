from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.allergens import Allergen
from app.menu.queries import get_item, get_items_by_ids
from app.menu.schemas import MenuFilter
from tests.contexts import corner_items, restaurant_row, tool_context


async def names(session: AsyncSession, menu_filter: MenuFilter) -> set[str]:
    return {item.name for item in await corner_items(session, menu_filter)}


async def test_empty_filter_returns_whole_menu_by_price(seeded: AsyncSession) -> None:
    items = await corner_items(seeded, MenuFilter())
    assert len(items) == 18
    assert [i.price_sar for i in items] == sorted(i.price_sar for i in items)


async def test_category(seeded: AsyncSession) -> None:
    items = await corner_items(seeded, MenuFilter(category="starters"))
    assert len(items) == 4
    assert {i.category for i in items} == {"starters"}


async def test_max_price(seeded: AsyncSession) -> None:
    found = await names(seeded, MenuFilter(max_price_sar=Decimal("22.00")))
    assert found == {"Fresh Lemon Mint", "Edamame with Chili Salt", "Mango Sorbet"}


async def test_max_spice(seeded: AsyncSession) -> None:
    items = await corner_items(seeded, MenuFilter(max_spice=0))
    assert items
    assert all(i.spice_level == 0 for i in items)


async def test_vegetarian_and_vegan(seeded: AsyncSession) -> None:
    assert len(await corner_items(seeded, MenuFilter(vegetarian=True))) == 12
    assert len(await corner_items(seeded, MenuFilter(vegan=True))) == 7


async def test_exclude_allergens_removes_every_match(seeded: AsyncSession) -> None:
    excluded = [Allergen.TREE_NUT, Allergen.PEANUT]
    items = await corner_items(seeded, MenuFilter(exclude_allergens=excluded))
    found = {i.name for i in items}
    assert "Pesto Penne" not in found
    assert "Thai Peanut Noodle Bowl" not in found
    assert "Pistachio Cheesecake" not in found
    assert all(not set(i.allergens) & {"tree_nut", "peanut"} for i in items)


async def test_may_contain_is_not_a_hard_exclusion(seeded: AsyncSession) -> None:
    """May-contain items get a warning in phase 4; the query does not remove them."""
    found = await names(seeded, MenuFilter(exclude_allergens=[Allergen.TREE_NUT]))
    assert "Chocolate Lava Cake" in found


async def test_text_matches_name_description_and_ingredients(seeded: AsyncSession) -> None:
    assert await names(seeded, MenuFilter(text="wagyu")) == {"Double Wagyu Burger"}
    assert await names(seeded, MenuFilter(text="molten")) == {"Chocolate Lava Cake"}
    assert await names(seeded, MenuFilter(text="PINE NUTS")) == {"Pesto Penne"}


async def test_text_matches_category(seeded: AsyncSession) -> None:
    found = await names(seeded, MenuFilter(text="pasta"))
    assert {"Pesto Penne", "Penne Arrabbiata", "Mediterranean Veggie Bowl"} <= found
    assert len(await names(seeded, MenuFilter(text="dessert"))) == 4


async def test_text_wildcards_are_literal(seeded: AsyncSession) -> None:
    assert await names(seeded, MenuFilter(text="%")) == set()
    assert await names(seeded, MenuFilter(text="_")) == set()


async def test_combined_filter(seeded: AsyncSession) -> None:
    menu_filter = MenuFilter(vegan=True, exclude_allergens=[Allergen.PEANUT], max_spice=1)
    assert await names(seeded, menu_filter) == {
        "Edamame with Chili Salt",
        "Plant-Based Burger",
        "Mediterranean Veggie Bowl",
        "Mango Sorbet",
        "Fresh Lemon Mint",
    }


async def test_no_match_is_empty_list(seeded: AsyncSession) -> None:
    menu_filter = MenuFilter(vegan=True, category="starters", max_price_sar=Decimal("10"))
    assert list(await corner_items(seeded, menu_filter)) == []


async def test_get_item_unknown_id_is_none(seeded: AsyncSession) -> None:
    corner = await restaurant_row(seeded)
    assert await get_item(seeded, corner.id, 999_999) is None


async def test_get_items_by_ids_drops_unknown_and_keeps_order(seeded: AsyncSession) -> None:
    corner = await restaurant_row(seeded)
    items = await corner_items(seeded)
    first, second = items[0].id, items[1].id
    result = await get_items_by_ids(seeded, corner.id, [second, 999_999, first, second])
    assert [i.id for i in result] == [second, first]
    assert list(await get_items_by_ids(seeded, corner.id, [])) == []


async def test_other_restaurants_items_are_not_found(seeded: AsyncSession) -> None:
    """Every read is scoped: a Corner Table ID does not exist anywhere else."""
    elsewhere = (await tool_context(seeded)).restaurant_id + 10_000
    item_id = (await corner_items(seeded))[0].id
    assert await get_item(seeded, elsewhere, item_id) is None
    assert list(await get_items_by_ids(seeded, elsewhere, [item_id])) == []
