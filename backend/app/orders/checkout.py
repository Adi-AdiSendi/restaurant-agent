"""Turn the guest's cart into an order. Only the guest's own button calls this (ADR 0019).

The cart row is locked, so a double click places one order: the second call
finds the cart empty. Prices and conflicts are worked out again here, since
the menu or the guest's profile may have changed since the dish was added.
With `expected_total`, the total the guest saw, a cart that changed meanwhile
(say, by a chat turn holding the cart lock) is refused instead of ordered.
"""

from collections.abc import Collection
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.constraints import HardConstraints
from app.orders.cart import own_cart
from app.orders.errors import CartChanged, EmptyCart, LineConflict, UnavailableLines
from app.orders.lines import Resolved, resolve
from app.orders.models import Order, OrderLine
from app.orders.orders import get_order
from app.orders.schemas import Fulfilment, OrderOut


def _snapshot(r: Resolved) -> OrderLine:
    assert r.item is not None and r.config is not None, "unavailable lines are refused first"
    offered = {o.id: o.name for g in r.item.option_groups for o in g.options}
    return OrderLine(
        item_id=r.item.id,
        item_name=r.item.name,
        category=r.item.category,
        quantity=r.line.quantity,
        unit_price_sar=r.config.unit_price_sar,
        option_names=[offered[i] for i in r.config.option_ids],
        removed=r.config.removed,
        allergens=[a.value for a in r.config.allergens],
        kcal=r.config.kcal,
    )


async def place_order(
    session: AsyncSession,
    user_id: int,
    fulfilment: Fulfilment,
    constraints: HardConstraints,
    *,
    accepted_reasons: Collection[str] = (),
    expected_total: Decimal | None = None,
) -> OrderOut:
    cart = await own_cart(session, user_id, lock=True)
    if cart is None or not cart.lines:
        raise EmptyCart("Your cart is empty.")
    resolved = await resolve(session, cart)
    if any(r.problem for r in resolved):
        raise UnavailableLines("Some dishes changed on the menu. Remove them, then try again.")
    lines = [_snapshot(r) for r in resolved]
    total = sum((ln.unit_price_sar * ln.quantity for ln in lines), Decimal(0))
    if expected_total is not None and total != expected_total:
        raise CartChanged("Your cart changed since you looked. Check it, then place the order.")
    reasons = sorted(
        {reason for r in resolved if r.config for reason in constraints.violations(r.config)}
    )
    if not set(reasons) <= set(accepted_reasons):
        raise LineConflict(
            f"Your cart has dishes that are not suitable: {', '.join(reasons)}.", reasons
        )
    order = Order(
        user_id=user_id,
        restaurant_id=cart.restaurant_id,
        fulfilment=fulfilment,
        total_sar=total,
        lines=lines,
    )
    session.add(order)
    cart.lines.clear()
    await session.flush()
    await session.refresh(order, ["placed_at"])
    return await get_order(session, user_id, order.id)
