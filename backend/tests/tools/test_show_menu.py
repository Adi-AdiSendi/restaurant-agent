import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.grounding import ids_in_tool_result
from app.agent.turn_reply import menus_from
from app.menu.allergens import Allergen
from app.tools import show_menu
from app.tools.errors import ToolError
from app.tools.show_menu import ShowMenuResult
from tests.contexts import tool_context
from tests.factories import guest


async def test_every_dish_in_the_category_with_unsuitable_ones_marked(
    seeded: AsyncSession,
) -> None:
    context = await tool_context(seeded, guest(Allergen.DAIRY), "bean-and-bloom")
    result = await show_menu.handle(json.dumps({"category": "coffee"}), context)
    assert isinstance(result, ShowMenuResult) and result.category == "coffee"
    assert {item.category for item in result.items} == {"coffee"}
    names = {item.name for item in result.items}
    assert "Latte" in names
    marked = {item.name for item in result.items if item.conflicts_with_guest}
    unmarked = names - marked
    assert unmarked, "a dairy guest can still order some coffee"
    [block] = menus_from([result])
    assert [card.name for card in block.items] == [item.name for item in result.items]
    assert ids_in_tool_result(result) == {item.id for item in result.items}


async def test_an_unknown_category_lists_the_real_ones(seeded: AsyncSession) -> None:
    context = await tool_context(seeded, slug="bean-and-bloom")
    result = await show_menu.handle(json.dumps({"category": "burgers"}), context)
    assert isinstance(result, ToolError) and result.error_category == "invalid_arguments"
    assert "coffee" in result.message


async def test_a_category_shown_twice_is_one_block(seeded: AsyncSession) -> None:
    context = await tool_context(seeded, slug="bean-and-bloom")
    first = await show_menu.handle(json.dumps({"category": "coffee"}), context)
    again = await show_menu.handle(json.dumps({"category": "coffee"}), context)
    assert len(menus_from([first, again])) == 1
