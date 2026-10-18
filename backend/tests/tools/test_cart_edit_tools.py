from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.allergens import Allergen
from app.orders.cart_add import add_line
from app.orders.checkout import place_order
from app.orders.orders import list_orders
from app.orders.schemas import NewLine
from app.tools import (
    add_to_cart,
    propose_checkout,
    recent_orders,
    remove_cart_line,
    update_cart_line,
    view_cart,
)
from app.tools.cart_results import CartChange, CartView, CheckoutProposal, RecentOrders
from app.tools.context import ToolContext
from app.tools.errors import ToolError
from tests.conftest import make_user
from tests.factories import guest
from tests.tools.cart_tool_helpers import BURGERS, CAFE, call, guest_context, latte_args

DAIRY = guest(Allergen.DAIRY)


async def _with_latte(session: AsyncSession, username: str) -> tuple[ToolContext, int]:
    context = await guest_context(session, await make_user(session, username))
    added = await call(add_to_cart, context, **await latte_args(session))
    assert isinstance(added, CartChange) and added.line is not None
    return context, added.line.id


async def test_view_cart_shows_the_lines(seeded: AsyncSession) -> None:
    context, line_id = await _with_latte(seeded, "chat_view")
    result = await call(view_cart, context)
    assert isinstance(result, CartView) and [line.id for line in result.cart.lines] == [line_id]


async def test_a_line_quantity_is_set_not_added(seeded: AsyncSession) -> None:
    context, line_id = await _with_latte(seeded, "chat_qty")
    result = await call(update_cart_line, context, line_id=line_id, quantity=3)
    assert isinstance(result, CartChange) and result.action == "updated"
    assert result.line is not None and result.line.quantity == 3 and result.cart.item_count == 3


async def test_a_removed_line_is_reported_as_it_was(seeded: AsyncSession) -> None:
    context, line_id = await _with_latte(seeded, "chat_remove")
    result = await call(remove_cart_line, context, line_id=line_id)
    assert isinstance(result, CartChange) and result.action == "removed"
    assert result.line is not None and result.line.name == "Latte"
    assert result.cart.lines == []


async def test_another_guests_line_cannot_be_changed(seeded: AsyncSession) -> None:
    _, line_id = await _with_latte(seeded, "chat_owner")
    stranger = await guest_context(seeded, await make_user(seeded, "chat_stranger"))
    for tool, args in (
        (update_cart_line, {"line_id": line_id, "quantity": 2}),
        (remove_cart_line, {"line_id": line_id}),
    ):
        result = await call(tool, stranger, **args)
        assert isinstance(result, ToolError) and result.error_category == "not_found"


async def test_checkout_is_proposed_and_never_placed(seeded: AsyncSession) -> None:
    context, _ = await _with_latte(seeded, "chat_checkout")
    result = await call(propose_checkout, context)
    assert isinstance(result, CheckoutProposal) and "Never say the order is placed" in result.note
    assert await list_orders(seeded, context.user_id) == []


async def test_checkout_of_an_empty_cart_is_refused(seeded: AsyncSession) -> None:
    context = await guest_context(seeded, await make_user(seeded, "chat_empty"))
    result = await call(propose_checkout, context)
    assert isinstance(result, ToolError) and result.error_category == "empty_cart"


async def test_recent_orders_are_the_guests_own_with_their_lines(seeded: AsyncSession) -> None:
    context, _ = await _with_latte(seeded, "chat_history")
    await place_order(seeded, context.user_id, "pickup", context.constraints)
    other = await guest_context(seeded, await make_user(seeded, "chat_nohistory"))
    mine = await call(recent_orders, context)
    assert isinstance(mine, RecentOrders) and len(mine.orders) == 1
    assert mine.orders[0].lines[0].item_name == "Latte"
    theirs = await call(recent_orders, other)
    assert isinstance(theirs, RecentOrders) and theirs.orders == []


async def test_tools_without_arguments_refuse_extra_ones(seeded: AsyncSession) -> None:
    context = await guest_context(seeded, await make_user(seeded, "chat_extra"))
    result = await call(view_cart, context, user_id=99)
    assert isinstance(result, ToolError) and result.error_category == "invalid_arguments"


async def test_a_line_that_breaks_the_profile_can_shrink_but_not_grow(
    seeded: AsyncSession,
) -> None:
    user = await make_user(seeded, "chat_consented")
    args = await latte_args(seeded, "Whole milk", quantity=2)
    del args["keep_ingredients"]  # a tool argument, not part of a cart line
    whole = NewLine.model_validate(args)
    cart = await add_line(seeded, user, CAFE, whole, DAIRY, accepted_reasons=["dairy"])
    line_id = cart.lines[0].id
    context = await guest_context(seeded, user, constraints=DAIRY)
    grown = await call(update_cart_line, context, line_id=line_id, quantity=3)
    assert isinstance(grown, ToolError) and grown.error_category == "conflict"
    shrunk = await call(update_cart_line, context, line_id=line_id, quantity=1)
    assert isinstance(shrunk, CartChange) and shrunk.cart.item_count == 1


async def test_checkout_is_only_proposed_at_the_carts_restaurant(seeded: AsyncSession) -> None:
    context, _ = await _with_latte(seeded, "chat_elsewhere")
    burgers = await guest_context(seeded, context.user_id, BURGERS)
    result = await call(propose_checkout, burgers)
    assert isinstance(result, ToolError) and result.error_category == "other_restaurant"
