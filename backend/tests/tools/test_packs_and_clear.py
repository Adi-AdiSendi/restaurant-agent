from sqlalchemy.ext.asyncio import AsyncSession

from app.orders.cart import get_cart
from app.tools import add_to_cart, clear_cart
from app.tools.cart_results import CartChange
from app.tools.errors import ToolError
from app.tools.packs import packs_for
from tests.conftest import make_user
from tests.factories import dish
from tests.orders.helpers import dish as seeded_dish
from tests.tools.cart_tool_helpers import BURGERS, call, guest_context, latte_args, smash_args

DATES = dish(name="Khalas Dates (box of 3)", pack_size=3, pack_unit="dates")


def test_whole_packs_are_counted_and_others_name_the_nearest() -> None:
    assert packs_for(DATES, 6) == 2
    five = packs_for(DATES, 5)
    assert isinstance(five, ToolError) and five.error_category == "needs_confirmation"
    assert "5 is not possible" in five.message
    assert "6 (2 packs) or 3 (1 pack)" in five.message
    two = packs_for(DATES, 2)
    assert isinstance(two, ToolError) and "nearest is 3 (1 pack)." in two.message


async def dates_args(session: AsyncSession, units: int) -> dict[str, object]:
    item_id, _ = await seeded_dish(session, "bean-and-bloom", "Khalas Dates (box of 3)")
    return {
        "item_id": item_id,
        "quantity": 1,
        "units": units,
        "option_ids": [],
        "removed": [],
        "keep_ingredients": [],
    }


async def test_five_dates_are_not_added_until_the_guest_picks_six(seeded: AsyncSession) -> None:
    user = await make_user(seeded, "packs_user")
    context = await guest_context(seeded, user)
    asked = await call(add_to_cart, context, **await dates_args(seeded, 5))
    assert isinstance(asked, ToolError) and asked.error_category == "needs_confirmation"
    assert (await get_cart(seeded, user, context.constraints)).lines == []
    agreed = await call(add_to_cart, context, **await dates_args(seeded, 6))
    assert isinstance(agreed, CartChange) and agreed.quantity == 2
    assert agreed.cart.total_sar == 18  # two boxes at 9.00


async def test_the_chat_can_empty_a_cart_and_fill_it_elsewhere(seeded: AsyncSession) -> None:
    user = await make_user(seeded, "clear_user")
    await call(add_to_cart, await guest_context(seeded, user), **await latte_args(seeded))
    burgers = await guest_context(seeded, user, BURGERS)
    cleared = await call(clear_cart, burgers)
    assert isinstance(cleared, CartChange) and cleared.action == "cleared"
    assert cleared.quantity == 1 and cleared.cart.lines == []
    added = await call(add_to_cart, burgers, **await smash_args(seeded))
    assert isinstance(added, CartChange) and added.cart.restaurant is not None
    assert added.cart.restaurant.slug == BURGERS
