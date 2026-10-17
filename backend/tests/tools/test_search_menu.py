import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.allergens import Allergen
from app.menu.constraints import NO_CONSTRAINTS, HardConstraints
from app.tools import search_menu
from app.tools.errors import ToolError
from app.tools.search_menu import SearchMenuResult
from tests.agent.fake_llm import EMPTY_SEARCH


async def run(
    session: AsyncSession, constraints: HardConstraints = NO_CONSTRAINTS, **overrides: object
) -> SearchMenuResult | ToolError:
    arguments = json.dumps(EMPTY_SEARCH | overrides)
    return await search_menu.handle(session, arguments, constraints)


async def test_filters_are_applied_in_sql(seeded: AsyncSession) -> None:
    result = await run(seeded, vegan=True, max_spice=1, exclude_allergens=["peanut"])
    assert isinstance(result, SearchMenuResult)
    assert result.items
    for item in result.items:
        assert item.is_vegan
        assert item.spice_level <= 1
        assert "peanut" not in item.allergens


async def test_results_carry_every_field_the_model_needs(seeded: AsyncSession) -> None:
    result = await run(seeded, text="salmon")
    assert isinstance(result, SearchMenuResult)
    fields = json.loads(result.model_dump_json())["items"][0]
    for name in ("id", "price_sar", "spice_level", "is_vegan", "allergens", "may_contain"):
        assert name in fields


async def test_no_match_is_success_with_empty_list(seeded: AsyncSession) -> None:
    result = await run(seeded, max_price_sar=1)
    assert result == SearchMenuResult(items=[])


async def test_bad_arguments_are_not_retryable(seeded: AsyncSession) -> None:
    result = await run(seeded, max_spice=9, exclude_allergens=["lactose"])
    assert isinstance(result, ToolError)
    assert result.error_category == "invalid_arguments"
    assert result.retryable is False
    assert "max_spice" in result.message
    assert "exclude_allergens" in result.message


async def test_malformed_json_is_invalid_arguments(seeded: AsyncSession) -> None:
    result = await search_menu.handle(seeded, "{not json", NO_CONSTRAINTS)
    assert isinstance(result, ToolError)
    assert result.error_category == "invalid_arguments"


@pytest.mark.parametrize("allergen", list(Allergen))
async def test_guest_allergy_is_applied_whatever_the_model_asks(
    seeded: AsyncSession, allergen: Allergen
) -> None:
    guest = HardConstraints(excluded_allergens=frozenset({allergen}))
    result = await run(seeded, guest, exclude_allergens=[], text=None)
    assert isinstance(result, SearchMenuResult)
    assert all(allergen not in item.allergens for item in result.items)
    assert result.guest_constraints_applied == guest


@pytest.mark.parametrize(
    ("guest", "flag"),
    [
        (HardConstraints(vegan=True), "is_vegan"),
        (HardConstraints(vegetarian=True), "is_vegetarian"),
    ],
)
async def test_guest_diet_is_applied_whatever_the_model_asks(
    seeded: AsyncSession, guest: HardConstraints, flag: str
) -> None:
    result = await run(seeded, guest, vegan=False, vegetarian=False)
    assert isinstance(result, SearchMenuResult)
    assert result.items
    assert all(getattr(item, flag) for item in result.items)
