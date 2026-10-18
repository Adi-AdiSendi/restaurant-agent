from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.allergens import Allergen
from app.menu.models import Option
from app.orders.cart import get_cart
from app.orders.cart_add import add_line
from app.orders.checkout import place_order
from app.orders.errors import CartChanged, EmptyCart, LineConflict, NotFound, UnavailableLines
from app.orders.orders import get_order, list_orders
from app.orders.schemas import NewLine
from app.orders.status import order_status
from tests.conftest import make_user
from tests.factories import guest
from tests.orders.helpers import dish

CAFE = "bean-and-bloom"
ANYONE = guest()


async def latte_line(session: AsyncSession, milk: str, *extra: str, quantity: int = 1) -> NewLine:
    item_id, options = await dish(session, CAFE, "Latte")
    chosen = [options["Medium"], options[milk], *(options[e] for e in extra)]
    return NewLine(item_id=item_id, quantity=quantity, option_ids=chosen, removed=[])


async def test_an_order_snapshots_the_cart_and_empties_it(seeded: AsyncSession) -> None:
    user = await make_user(seeded, "chk_a")
    line = await latte_line(seeded, "Oat milk", "Vanilla", quantity=2)
    await add_line(seeded, user, CAFE, line, ANYONE)
    order = await place_order(seeded, user, "pickup", ANYONE)
    assert order.total_sar == Decimal("48.00")  # (16 + medium 3 + oat 3 + vanilla 2) x 2
    [snap] = order.lines
    assert (snap.item_name, snap.quantity, snap.unit_price_sar) == ("Latte", 2, Decimal("24.00"))
    assert snap.option_names == ["Medium", "Oat milk", "Vanilla"]
    assert order.status == "placed" and order.fulfilment == "pickup"
    assert order.restaurant.slug == CAFE
    assert (await get_cart(seeded, user, ANYONE)).lines == []


async def test_a_second_click_finds_the_cart_empty(seeded: AsyncSession) -> None:
    user = await make_user(seeded, "chk_b")
    await add_line(seeded, user, CAFE, await latte_line(seeded, "Oat milk"), ANYONE)
    await place_order(seeded, user, "dine_in", ANYONE)
    with pytest.raises(EmptyCart):
        await place_order(seeded, user, "dine_in", ANYONE)
    assert len(await list_orders(seeded, user)) == 1


async def test_a_conflict_that_appeared_after_the_add_needs_consent(seeded: AsyncSession) -> None:
    user = await make_user(seeded, "chk_c")
    await add_line(seeded, user, CAFE, await latte_line(seeded, "Whole milk"), ANYONE)
    dairy = guest(Allergen.DAIRY)  # the guest said "I'm allergic to dairy" after adding it
    with pytest.raises(LineConflict) as refused:
        await place_order(seeded, user, "pickup", dairy)
    assert refused.value.reasons == ["dairy"]
    with pytest.raises(LineConflict):
        await place_order(seeded, user, "pickup", dairy, accepted_reasons=["not vegan"])
    order = await place_order(seeded, user, "pickup", dairy, accepted_reasons=["dairy"])
    assert order.lines[0].allergens == ["dairy"]


async def test_unavailable_lines_block_checkout(seeded: AsyncSession) -> None:
    user = await make_user(seeded, "chk_d")
    line = await latte_line(seeded, "Oat milk")
    await add_line(seeded, user, CAFE, line, ANYONE)
    await seeded.execute(delete(Option).where(Option.id == line.option_ids[1]))
    seeded.expire_all()
    with pytest.raises(UnavailableLines):
        await place_order(seeded, user, "pickup", ANYONE)


async def test_orders_are_listed_newest_first_and_private(seeded: AsyncSession) -> None:
    alice, bob = await make_user(seeded, "chk_e"), await make_user(seeded, "chk_f")
    with pytest.raises(EmptyCart):
        await place_order(seeded, alice, "pickup", ANYONE)
    ids: list[int] = []
    for milk in ("Oat milk", "Soy milk"):
        await add_line(seeded, alice, CAFE, await latte_line(seeded, milk), ANYONE)
        ids.append((await place_order(seeded, alice, "pickup", ANYONE)).id)
    assert [o.id for o in await list_orders(seeded, alice)] == sorted(ids, reverse=True)
    assert await list_orders(seeded, bob) == []
    with pytest.raises(NotFound):
        await get_order(seeded, bob, ids[0])


@pytest.mark.parametrize(
    ("minutes", "status"),
    [(0, "placed"), (1.9, "placed"), (2, "preparing"), (11.9, "preparing"), (12, "ready")],
)
def test_status_follows_the_time_since_placing(minutes: float, status: str) -> None:
    placed = datetime(2026, 10, 17, 12, 0, tzinfo=UTC)
    assert order_status(placed, placed + timedelta(minutes=minutes)) == status


async def test_a_cart_that_changed_since_the_guest_looked_is_not_ordered(
    seeded: AsyncSession,
) -> None:
    user = await make_user(seeded, "checkout_changed")
    cart = await add_line(seeded, user, CAFE, await latte_line(seeded, "Oat milk"), ANYONE)
    seen = cart.total_sar
    await add_line(seeded, user, CAFE, await latte_line(seeded, "Oat milk"), ANYONE)
    with pytest.raises(CartChanged):
        await place_order(seeded, user, "pickup", ANYONE, expected_total=seen)
    assert await list_orders(seeded, user) == []
    order = await place_order(seeded, user, "pickup", ANYONE, expected_total=seen * 2)
    assert order.total_sar == seen * 2
