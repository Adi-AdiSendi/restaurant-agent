"""The menu tools at a restaurant with options, and their restaurant scoping."""

import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.allergens import Allergen
from app.menu.constraints import HardConstraints
from app.tools import get_item, search_menu
from app.tools.errors import ToolError
from app.tools.get_item import GetItemResult
from app.tools.search_menu import SearchMenuResult
from scripts.menu_sync import sync_restaurant
from tests.agent.fake_llm import EMPTY_SEARCH
from tests.contexts import corner_items, tool_context
from tests.factories import TEST_CAFE, guest


async def search(
    session: AsyncSession, constraints: HardConstraints, **overrides: object
) -> SearchMenuResult | ToolError:
    context = await tool_context(session, constraints, slug="test-cafe")
    return await search_menu.handle(json.dumps(EMPTY_SEARCH | overrides), context)


async def test_an_item_with_one_fitting_choice_is_found_with_option_conflicts(
    session: AsyncSession,
) -> None:
    await sync_restaurant(session, TEST_CAFE, 9)
    result = await search(session, guest(Allergen.DAIRY))
    assert isinstance(result, SearchMenuResult)
    [latte] = result.items
    conflicts = {o.name: o.conflicts_with_guest for o in latte.option_groups[0].options}
    assert conflicts == {"Whole milk": ["dairy"], "Oat milk": []}


async def test_an_item_with_no_fitting_choice_is_not_found(session: AsyncSession) -> None:
    await sync_restaurant(session, TEST_CAFE, 9)
    result = await search(session, guest(Allergen.DAIRY, Allergen.GLUTEN))
    assert result == SearchMenuResult(
        items=[], guest_constraints_applied=guest(Allergen.DAIRY, Allergen.GLUTEN)
    )


async def test_get_item_explains_why_no_choice_fits(session: AsyncSession) -> None:
    await sync_restaurant(session, TEST_CAFE, 9)
    context = await tool_context(session, guest(Allergen.DAIRY, Allergen.GLUTEN), "test-cafe")
    found = await search(session, guest())
    assert isinstance(found, SearchMenuResult)
    result = await get_item.handle(json.dumps({"item_id": found.items[0].id}), context)
    assert isinstance(result, GetItemResult)
    assert result.conflicts_with_guest == ["no milk choice fits"]


async def test_unknown_category_lists_this_restaurants_categories(session: AsyncSession) -> None:
    await sync_restaurant(session, TEST_CAFE, 9)
    result = await search(session, guest(), category="starters")
    assert isinstance(result, ToolError)
    assert result.error_category == "invalid_arguments"
    assert "Use one of: coffee, or null." in result.message


async def test_another_restaurants_item_is_not_found(seeded: AsyncSession) -> None:
    await sync_restaurant(seeded, TEST_CAFE, 9)
    corner_dish = (await corner_items(seeded))[0].id
    context = await tool_context(seeded, guest(), "test-cafe")
    result = await get_item.handle(json.dumps({"item_id": corner_dish}), context)
    assert isinstance(result, ToolError)
    assert result.error_category == "not_found"
    found = await search(seeded, guest())
    assert isinstance(found, SearchMenuResult)
    assert {i.name for i in found.items} == {"Latte"}


async def test_the_models_own_filter_also_checks_options(session: AsyncSession) -> None:
    """No saved profile, but the model asks for dairy- and gluten-free: no milk fits."""
    await sync_restaurant(session, TEST_CAFE, 9)
    result = await search(session, guest(), exclude_allergens=["dairy", "gluten"])
    assert isinstance(result, SearchMenuResult)
    assert result.items == []


async def test_text_search_matches_option_names(session: AsyncSession) -> None:
    await sync_restaurant(session, TEST_CAFE, 9)
    result = await search(session, guest(), text="oat")
    assert isinstance(result, SearchMenuResult)
    assert [i.name for i in result.items] == ["Latte"]
