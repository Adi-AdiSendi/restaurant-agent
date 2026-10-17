"""Change, remove or clear lines of the guest's own cart. Another user's line is not found."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.constraints import HardConstraints
from app.orders.cart import EMPTY, get_cart, own_cart
from app.orders.errors import InvalidChoice, NotFound
from app.orders.models import Cart, CartLine
from app.orders.schemas import MAX_QUANTITY, CartOut


async def set_quantity(
    session: AsyncSession, user_id: int, line_id: int, quantity: int, constraints: HardConstraints
) -> CartOut:
    if not 1 <= quantity <= MAX_QUANTITY:
        raise InvalidChoice(f"Quantity must be 1 to {MAX_QUANTITY}.")
    _, line = await _own_line(session, user_id, line_id)
    line.quantity = quantity
    await session.flush()
    return await get_cart(session, user_id, constraints)


async def remove_line(
    session: AsyncSession, user_id: int, line_id: int, constraints: HardConstraints
) -> CartOut:
    cart, line = await _own_line(session, user_id, line_id)
    cart.lines.remove(line)
    await session.flush()
    return await get_cart(session, user_id, constraints)


async def clear_cart(session: AsyncSession, user_id: int) -> CartOut:
    cart = await own_cart(session, user_id, lock=True)
    if cart is not None:
        cart.lines.clear()
        await session.flush()
    return EMPTY


async def _own_line(session: AsyncSession, user_id: int, line_id: int) -> tuple[Cart, CartLine]:
    cart = await own_cart(session, user_id, lock=True)
    line = next((ln for ln in cart.lines if ln.id == line_id), None) if cart else None
    if cart is None or line is None:
        raise NotFound("That line is not in your cart.")
    return cart, line
