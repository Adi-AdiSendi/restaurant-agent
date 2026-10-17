"""Place an order from the cart, and read the guest's own orders. No payment (ADR 0019)."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
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
    accept_conflicts: bool = False
    """The guest saw the allergy or diet warnings at checkout and still wants to order."""


@router.post("/orders", status_code=201)
async def place(
    body: PlaceOrderRequest,
    user_id: int = Depends(current_user_id),
    constraints: HardConstraints = Depends(guest_constraints),
    session: AsyncSession = Depends(get_session),
) -> OrderOut:
    try:
        order = await place_order(
            session, user_id, body.fulfilment, constraints, accept_conflicts=body.accept_conflicts
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
