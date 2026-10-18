"""The guest's past orders. Another user's order is not found."""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.restaurant import Restaurant
from app.orders.errors import NotFound
from app.orders.models import Order, OrderLine
from app.orders.schemas import CartRestaurant, OrderLineOut, OrderOut, OrderSummary
from app.orders.status import order_status


def _summary(order: Order, restaurant: Restaurant, now: datetime) -> OrderSummary:
    return OrderSummary(
        id=order.id,
        restaurant=CartRestaurant(slug=restaurant.slug, name=restaurant.name),
        fulfilment="pickup" if order.fulfilment == "pickup" else "dine_in",
        total_sar=order.total_sar,
        item_count=sum(line.quantity for line in order.lines),
        placed_at=order.placed_at,
        status=order_status(order.placed_at, now),
    )


async def list_orders(session: AsyncSession, user_id: int) -> list[OrderSummary]:
    """Newest first."""
    stmt = (
        select(Order, Restaurant)
        .join(Restaurant, Restaurant.id == Order.restaurant_id)
        .where(Order.user_id == user_id)
        .order_by(Order.placed_at.desc(), Order.id.desc())
    )
    now = datetime.now(UTC)
    return [_summary(order, restaurant, now) for order, restaurant in await session.execute(stmt)]


async def get_order(session: AsyncSession, user_id: int, order_id: int) -> OrderOut:
    stmt = (
        select(Order, Restaurant)
        .join(Restaurant, Restaurant.id == Order.restaurant_id)
        .where(Order.id == order_id, Order.user_id == user_id)
    )
    found = (await session.execute(stmt)).one_or_none()
    if found is None:
        raise NotFound("No such order.")
    order, restaurant = found
    summary = _summary(order, restaurant, datetime.now(UTC))
    lines = [OrderLineOut.model_validate(line) for line in order.lines]
    return OrderOut(**summary.model_dump(), lines=lines)


async def kcal_since(session: AsyncSession, user_id: int, since: datetime) -> int:
    """Estimated kcal of this guest's orders placed since `since`, for the daily goal."""
    stmt = (
        select(func.coalesce(func.sum(OrderLine.kcal * OrderLine.quantity), 0))
        .join(Order, Order.id == OrderLine.order_id)
        .where(Order.user_id == user_id, Order.placed_at >= since)
    )
    return int(await session.scalar(stmt) or 0)
