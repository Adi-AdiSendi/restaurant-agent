"""Place an order from the cart, and read the guest's own orders. No payment (ADR 0019)."""

from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user_id, guest_constraints
from app.api.order_errors import http_error
from app.db.engine import get_session
from app.menu.constraints import HardConstraints
from app.orders.checkout import place_order
from app.orders.errors import OrderError
from app.orders.orders import get_order, list_orders
from app.orders.schemas import Fulfilment, OrderOut, OrderSummary

router = APIRouter()


class PlaceOrderRequest(BaseModel):
    fulfilment: Fulfilment
    accepted_reasons: list[str] = Field(default_factory=list[str], max_length=20)
    """The conflict reasons the guest was shown at checkout and accepted."""
    expected_total_sar: Decimal | None = None
    """The total the guest saw; a cart that changed since is refused (code cart_changed)."""


@router.post("/orders", status_code=201)
async def place(
    body: PlaceOrderRequest,
    user_id: int = Depends(current_user_id),
    constraints: HardConstraints = Depends(guest_constraints),
    session: AsyncSession = Depends(get_session),
) -> OrderOut:
    try:
        order = await place_order(
            session,
            user_id,
            body.fulfilment,
            constraints,
            accepted_reasons=body.accepted_reasons,
            expected_total=body.expected_total_sar,
        )
    except OrderError as exc:
        raise http_error(exc) from exc
    await session.commit()
    return order


@router.get("/orders")
async def orders(
    user_id: int = Depends(current_user_id), session: AsyncSession = Depends(get_session)
) -> list[OrderSummary]:
    return await list_orders(session, user_id)


@router.get("/orders/{order_id}")
async def order(
    order_id: int,
    user_id: int = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> OrderOut:
    try:
        return await get_order(session, user_id, order_id)
    except OrderError as exc:
        raise http_error(exc) from exc
