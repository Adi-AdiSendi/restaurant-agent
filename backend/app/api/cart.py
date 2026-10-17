"""The logged-in guest's cart. Prices come from the server; the body never carries one."""

from collections.abc import Awaitable

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user_id, guest_constraints
from app.api.order_errors import http_error
from app.db.engine import get_session
from app.menu.constraints import HardConstraints
from app.orders.cart import get_cart
from app.orders.cart_add import add_line
from app.orders.cart_edit import clear_cart, remove_line, set_quantity
from app.orders.errors import OrderError
from app.orders.schemas import MAX_QUANTITY, CartOut, NewLine

router = APIRouter()


class AddLineRequest(NewLine):
    restaurant: str = Field(max_length=40)
    accepted_reasons: list[str] = Field(default_factory=list[str], max_length=20)
    """The conflict reasons the guest was shown and accepted; any other conflict asks again."""
    replace_cart: bool = False
    """The guest agreed to empty a cart from another restaurant."""


class QuantityRequest(BaseModel):
    quantity: int = Field(ge=1, le=MAX_QUANTITY)


async def _saved(session: AsyncSession, change: Awaitable[CartOut]) -> CartOut:
    """Run one cart change, map its domain error to HTTP, commit if it worked."""
    try:
        result = await change
    except OrderError as exc:
        raise http_error(exc) from exc
    await session.commit()
    return result


@router.get("/cart")
async def cart(
    user_id: int = Depends(current_user_id),
    constraints: HardConstraints = Depends(guest_constraints),
    session: AsyncSession = Depends(get_session),
) -> CartOut:
    return await get_cart(session, user_id, constraints)


@router.post("/cart/lines")
async def add(
    body: AddLineRequest,
    user_id: int = Depends(current_user_id),
    constraints: HardConstraints = Depends(guest_constraints),
    session: AsyncSession = Depends(get_session),
) -> CartOut:
    line = NewLine(**body.model_dump(include=set(NewLine.model_fields)))
    change = add_line(
        session,
        user_id,
        body.restaurant,
        line,
        constraints,
        accepted_reasons=body.accepted_reasons,
        replace_cart=body.replace_cart,
    )
    return await _saved(session, change)


@router.patch("/cart/lines/{line_id}")
async def change(
    line_id: int,
    body: QuantityRequest,
    user_id: int = Depends(current_user_id),
    constraints: HardConstraints = Depends(guest_constraints),
    session: AsyncSession = Depends(get_session),
) -> CartOut:
    change = set_quantity(session, user_id, line_id, body.quantity, constraints)
    return await _saved(session, change)


@router.delete("/cart/lines/{line_id}")
async def remove(
    line_id: int,
    user_id: int = Depends(current_user_id),
    constraints: HardConstraints = Depends(guest_constraints),
    session: AsyncSession = Depends(get_session),
) -> CartOut:
    return await _saved(session, remove_line(session, user_id, line_id, constraints))


@router.delete("/cart")
async def clear(
    user_id: int = Depends(current_user_id), session: AsyncSession = Depends(get_session)
) -> CartOut:
    return await _saved(session, clear_cart(session, user_id))
