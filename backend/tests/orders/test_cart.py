from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.allergens import Allergen
from app.menu.models import MenuItem, Option
from app.orders.cart import get_cart
from app.orders.cart_add import add_line
from app.orders.cart_edit import clear_cart, remove_line, set_quantity
from app.orders.errors import InvalidChoice, LineConflict, NotFound, OtherRestaurant
from app.orders.schemas import NewLine
from tests.conftest import make_user
from tests.factories import guest
from tests.orders.helpers import dish

CAFE = "bean-and-bloom"
ANYONE = guest()


async def latte(session: AsyncSession, *milks: str, quantity: int = 1) -> NewLine:
    item_id, options = await dish(session, CAFE, "Latte")
    small = options["Small"]
    return NewLine(
        item_id=item_id, quantity=quantity, option_ids=[small] + [options[m] for m in milks]
    )


async def test_the_server_prices_every_line(seeded: AsyncSession) -> None:
    user = await make_user(seeded, "cart_a")
    cart = await add_line(seeded, user, CAFE, await latte(seeded, "Oat milk", quantity=2), ANYONE)
    [line] = cart.lines
    assert line.unit_price_sar == Decimal("19.00")  # 16 + small 0 + oat 3
    assert cart.total_sar == Decimal("38.00") and cart.item_count == 2
    assert [o.name for o in line.options] == ["Small", "Oat milk"]
    assert cart.restaurant is not None and cart.restaurant.slug == CAFE


def test_a_client_cannot_send_a_price() -> None:
    with pytest.raises(ValidationError):
        NewLine.model_validate({"item_id": 1, "price_sar": "1.00"})


async def test_invalid_choices_and_unknown_dishes_are_refused(seeded: AsyncSession) -> None:
    user = await make_user(seeded, "cart_b")
    no_milk = await latte(seeded)
    with pytest.raises(InvalidChoice, match="Milk"):
        await add_line(seeded, user, CAFE, no_milk, ANYONE)
    bad_removal = (await latte(seeded, "Oat milk")).model_copy(update={"removed": ["espresso"]})
    with pytest.raises(InvalidChoice, match="cannot be left out"):
        await add_line(seeded, user, CAFE, bad_removal, ANYONE)
    with pytest.raises(NotFound):
        await add_line(seeded, user, "corner-table", await latte(seeded, "Oat milk"), ANYONE)


async def test_a_conflict_needs_the_guests_acknowledgement(seeded: AsyncSession) -> None:
    user = await make_user(seeded, "cart_c")
    whole = await latte(seeded, "Whole milk")
    with pytest.raises(LineConflict) as refused:
        await add_line(seeded, user, CAFE, whole, guest(Allergen.DAIRY))
    assert refused.value.reasons == ["dairy"]
    assert (await get_cart(seeded, user, guest(Allergen.DAIRY))).lines == []
    cart = await add_line(seeded, user, CAFE, whole, guest(Allergen.DAIRY), accept_conflict=True)
    assert cart.lines[0].conflicts_with_guest == ["dairy"]


async def test_the_same_choice_adds_up_to_twenty(seeded: AsyncSession) -> None:
    user = await make_user(seeded, "cart_d")
    await add_line(seeded, user, CAFE, await latte(seeded, "Oat milk", quantity=12), ANYONE)
    cart = await add_line(seeded, user, CAFE, await latte(seeded, "Oat milk", quantity=8), ANYONE)
    assert [ln.quantity for ln in cart.lines] == [20]
    with pytest.raises(InvalidChoice, match="At most 20"):
        await add_line(seeded, user, CAFE, await latte(seeded, "Oat milk"), ANYONE)


async def test_another_restaurant_needs_consent_to_replace_the_cart(seeded: AsyncSession) -> None:
    user = await make_user(seeded, "cart_e")
    await add_line(seeded, user, CAFE, await latte(seeded, "Oat milk"), ANYONE)
    sorbet, _ = await dish(seeded, "corner-table", "Mango Sorbet")
    with pytest.raises(OtherRestaurant, match="Bean & Bloom"):
        await add_line(seeded, user, "corner-table", NewLine(item_id=sorbet), ANYONE)
    cart = await add_line(
        seeded, user, "corner-table", NewLine(item_id=sorbet), ANYONE, replace_cart=True
    )
    assert cart.restaurant is not None and cart.restaurant.slug == "corner-table"
    assert [ln.name for ln in cart.lines] == ["Mango Sorbet"]


async def test_lines_belong_to_their_user(seeded: AsyncSession) -> None:
    alice, bob = await make_user(seeded, "cart_f"), await make_user(seeded, "cart_g")
    cart = await add_line(seeded, alice, CAFE, await latte(seeded, "Oat milk"), ANYONE)
    line_id = cart.lines[0].id
    for change in (
        set_quantity(seeded, bob, line_id, 3, ANYONE),
        remove_line(seeded, bob, line_id, ANYONE),
    ):
        with pytest.raises(NotFound):
            await change
    assert (await get_cart(seeded, bob, ANYONE)).lines == []
    assert (await set_quantity(seeded, alice, line_id, 3, ANYONE)).item_count == 3
    with pytest.raises(InvalidChoice):
        await set_quantity(seeded, alice, line_id, 21, ANYONE)
    assert (await remove_line(seeded, alice, line_id, ANYONE)).lines == []


async def test_a_menu_change_makes_a_line_unavailable(seeded: AsyncSession) -> None:
    user = await make_user(seeded, "cart_h")
    oat = await latte(seeded, "Oat milk")
    await add_line(seeded, user, CAFE, oat, ANYONE)
    await seeded.execute(delete(Option).where(Option.id == oat.option_ids[1]))
    seeded.expire_all()
    cart = await get_cart(seeded, user, ANYONE)
    assert cart.lines[0].problem is not None and cart.lines[0].unit_price_sar is None
    assert cart.total_sar == 0
    await seeded.execute(delete(MenuItem).where(MenuItem.id == oat.item_id))
    seeded.expire_all()
    assert (await get_cart(seeded, user, ANYONE)).lines == []
    assert (await clear_cart(seeded, user)).lines == []
