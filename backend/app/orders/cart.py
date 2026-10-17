"""The guest's one open cart, as they see it now. Scoped by the session user's ID.

Lines are resolved against today's menu on every read (`lines.py`).
"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.constraints import HardConstraints
from app.menu.queries import get_restaurant
from app.orders.lines import line_out, resolve, total
from app.orders.models import Cart
from app.orders.schemas import CartOut, CartRestaurant

EMPTY = CartOut(restaurant=None, lines=[], total_sar=Decimal(0), item_count=0)


async def own_cart(session: AsyncSession, user_id: int, *, lock: bool = False) -> Cart | None:
    stmt = select(Cart).where(Cart.user_id == user_id)
    return await session.scalar(stmt.with_for_update() if lock else stmt)


async def get_cart(session: AsyncSession, user_id: int, constraints: HardConstraints) -> CartOut:
    cart = await own_cart(session, user_id)
    if cart is None or not cart.lines:
        return EMPTY
    restaurant = await get_restaurant(session, cart.restaurant_id)
    assert restaurant is not None, "carts.restaurant_id is a foreign key"
    lines = [line_out(r, constraints) for r in await resolve(session, cart)]
    return CartOut(
        restaurant=CartRestaurant(slug=restaurant.slug, name=restaurant.name),
        lines=lines,
        total_sar=total(lines),
        item_count=sum(ln.quantity for ln in lines),
    )
