from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.allergens import Allergen
from app.menu.constraints import NO_CONSTRAINTS, HardConstraints
from app.menu.schemas import MenuFilter
from app.tools import get_item
from app.tools.errors import ToolError
from app.tools.get_item import GetItemResult
from tests.contexts import corner_items, tool_context


async def item_id(session: AsyncSession, text: str) -> int:
    return (await corner_items(session, MenuFilter(text=text)))[0].id


async def test_known_id_returns_item(seeded: AsyncSession) -> None:
    first = (await corner_items(seeded, MenuFilter()))[0]
    result = await get_item.handle(
        f'{{"item_id": {first.id}}}', await tool_context(seeded, NO_CONSTRAINTS)
    )
    assert isinstance(result, GetItemResult)
    assert result.item.name == first.name
    assert result.conflicts_with_guest == []


async def test_conflicts_with_the_guest_are_reported_not_hidden(seeded: AsyncSession) -> None:
    """The agent may describe the item (ADR 0009) but sees why it must not recommend it."""
    thai = await item_id(seeded, "peanut sauce")
    guest = HardConstraints(excluded_allergens=frozenset({Allergen.PEANUT}), vegetarian=True)
    result = await get_item.handle(f'{{"item_id": {thai}}}', await tool_context(seeded, guest))
    assert isinstance(result, GetItemResult)
    assert result.conflicts_with_guest == ["peanut"]
    wings = await item_id(seeded, "wings")
    result = await get_item.handle(f'{{"item_id": {wings}}}', await tool_context(seeded, guest))
    assert isinstance(result, GetItemResult)
    assert result.conflicts_with_guest == ["not vegetarian"]


async def test_may_contain_is_a_warning_not_a_conflict(seeded: AsyncSession) -> None:
    cake = await item_id(seeded, "lava")
    guest = HardConstraints(excluded_allergens=frozenset({Allergen.TREE_NUT}))
    result = await get_item.handle(f'{{"item_id": {cake}}}', await tool_context(seeded, guest))
    assert isinstance(result, GetItemResult)
    assert result.conflicts_with_guest == []
    assert result.may_contain_warnings == [Allergen.TREE_NUT]


async def test_unknown_id_is_not_found(seeded: AsyncSession) -> None:
    result = await get_item.handle(
        '{"item_id": 999999}', await tool_context(seeded, NO_CONSTRAINTS)
    )
    assert result == ToolError(
        error_category="not_found",
        retryable=False,
        message="This restaurant has no menu item with id 999999.",
    )


async def test_bad_id_is_invalid_arguments(seeded: AsyncSession) -> None:
    result = await get_item.handle(
        '{"item_id": "seven"}', await tool_context(seeded, NO_CONSTRAINTS)
    )
    assert isinstance(result, ToolError)
    assert result.error_category == "invalid_arguments"
