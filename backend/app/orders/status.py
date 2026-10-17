"""An order's status, derived from how long ago it was placed. No background jobs."""

from datetime import datetime, timedelta

from app.orders.schemas import OrderStatus

PREPARING_AFTER = timedelta(minutes=2)
READY_AFTER = timedelta(minutes=12)


def order_status(placed_at: datetime, now: datetime) -> OrderStatus:
    age = now - placed_at
    if age < PREPARING_AFTER:
        return "placed"
    if age < READY_AFTER:
        return "preparing"
    return "ready"
