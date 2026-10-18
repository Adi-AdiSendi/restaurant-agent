from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.allergens import Allergen
from app.orders.cart import get_cart
from app.tools import add_to_cart
from app.tools.cart_results import CartChange
from app.tools.errors import ToolError
from tests.conftest import make_user
from tests.factories import guest
from tests.tools.cart_tool_helpers import (
    BURGERS,
    call,
    guest_context,
    latte_args,
    smash_args,
)

DAIRY = guest(Allergen.DAIRY)


async def test_an_add_is_priced_by_the_server_and_kept(seeded: AsyncSession) -> None:
    user = await make_user(seeded, "chat_add")
    context = await guest_context(seeded, user)
    result = await call(add_to_cart, context, **await latte_args(seeded, quantity=2))
    assert isinstance(result, CartChange) and result.action == "added"
    assert result.line is not None and result.line.unit_price_sar == Decimal("19.00")
    assert result.quantity == 2 and result.cart.total_sar == Decimal("38.00")
    assert (await get_cart(seeded, user, context.constraints)).item_count == 2


async def test_a_conflict_is_refused_and_the_turn_goes_on(seeded: AsyncSession) -> None:
    user = await make_user(seeded, "chat_dairy")
    context = await guest_context(seeded, user, constraints=DAIRY)
    refused = await call(add_to_cart, context, **await latte_args(seeded, "Whole milk"))
    assert isinstance(refused, ToolError) and refused.error_category == "conflict"
    assert "dairy" in refused.message and "Never offer to add it anyway" in refused.message
    assert not (await get_cart(seeded, user, DAIRY)).lines
    # The refusal leaves the session usable, so the turn can go on.
    added = await call(add_to_cart, context, **await latte_args(seeded))
    assert isinstance(added, CartChange) and added.cart.item_count == 1


async def test_a_missing_required_choice_is_an_invalid_choice(seeded: AsyncSession) -> None:
    context = await guest_context(seeded, await make_user(seeded, "chat_choice"))
    args = await latte_args(seeded)
    args["option_ids"] = []
    result = await call(add_to_cart, context, **args)
    assert isinstance(result, ToolError) and result.error_category == "invalid_choice"


async def test_an_unknown_or_foreign_item_is_not_found(seeded: AsyncSession) -> None:
    user = await make_user(seeded, "chat_foreign")
    context = await guest_context(seeded, user, BURGERS)
    result = await call(add_to_cart, context, **await latte_args(seeded))
    assert isinstance(result, ToolError) and result.error_category == "not_found"


async def test_bad_arguments_are_not_retryable(seeded: AsyncSession) -> None:
    context = await guest_context(seeded, await make_user(seeded, "chat_args"))
    result = await call(add_to_cart, context, item_id=1, quantity=0)
    assert isinstance(result, ToolError) and result.error_category == "invalid_arguments"
    assert not result.retryable


async def test_a_cart_at_another_restaurant_is_never_replaced(seeded: AsyncSession) -> None:
    user = await make_user(seeded, "chat_other")
    await call(add_to_cart, await guest_context(seeded, user), **await latte_args(seeded))
    burgers = await guest_context(seeded, user, BURGERS)
    result = await call(add_to_cart, burgers, **await smash_args(seeded))
    assert isinstance(result, ToolError) and result.error_category == "other_restaurant"
    assert "Bean & Bloom" in result.message and "clear_cart" in result.message
    cart = await get_cart(seeded, user, burgers.constraints)
    assert cart.restaurant is not None and cart.restaurant.name == "Bean & Bloom"


async def test_a_disliked_removable_ingredient_is_left_out(seeded: AsyncSession) -> None:
    user = await make_user(seeded, "chat_pickles")
    context = await guest_context(seeded, user, BURGERS, dislikes=("pickle", "mushrooms"))
    result = await call(add_to_cart, context, **await smash_args(seeded))
    assert isinstance(result, CartChange) and result.left_out_for_dislikes == ["pickles"]
    assert result.line is not None and result.line.removed == ["pickles"]


async def test_the_guest_can_keep_a_disliked_ingredient_this_time(seeded: AsyncSession) -> None:
    user = await make_user(seeded, "chat_keep")
    context = await guest_context(seeded, user, BURGERS, dislikes=("pickles",))
    result = await call(add_to_cart, context, **await smash_args(seeded, keep=["Pickles"]))
    assert isinstance(result, CartChange) and result.left_out_for_dislikes == []
    assert result.line is not None and result.line.removed == []
