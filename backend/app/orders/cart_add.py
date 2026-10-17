"""Add a configured dish to the guest's cart.

The cart row is locked for the write, so two quick adds (or a chat turn and a
click) cannot interleave. A choice that breaks the guest's saved allergies or
diet is only added when the guest has acknowledged it (ADR 0019).
"""

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.configure import ConfigurationError, configure
from app.menu.constraints import HardConstraints
from app.menu.queries import get_item, get_restaurant, restaurant_by_slug
from app.menu.schemas import MenuItemOut
from app.orders.cart import get_cart, own_cart
from app.orders.errors import InvalidChoice, LineConflict, NotFound, OtherRestaurant
from app.orders.models import Cart, CartLine
from app.orders.schemas import MAX_QUANTITY, CartOut, NewLine


async def add_line(
    session: AsyncSession,
    user_id: int,
    restaurant_slug: str,
    new: NewLine,
    constraints: HardConstraints,
    *,
    accept_conflict: bool = False,
    replace_cart: bool = False,
) -> CartOut:
    restaurant = await restaurant_by_slug(session, restaurant_slug)
    row = await get_item(session, restaurant.id, new.item_id) if restaurant else None
    if restaurant is None or row is None:
        raise NotFound("This restaurant has no such dish.")
    item = MenuItemOut.model_validate(row)
    try:
        config = configure(item, new.option_ids, new.removed)
    except ConfigurationError as exc:
        raise InvalidChoice(str(exc)) from exc
    reasons = constraints.violations(config)
    if reasons and not accept_conflict:
        raise LineConflict(f"{item.name} as chosen is not suitable: {', '.join(reasons)}.", reasons)

    # One cart row per user: create it if needed, then lock it for this write.
    await session.execute(
        insert(Cart)
        .values(user_id=user_id, restaurant_id=restaurant.id)
        .on_conflict_do_nothing(index_elements=["user_id"])
    )
    cart = await own_cart(session, user_id, lock=True)
    assert cart is not None
    if cart.restaurant_id != restaurant.id:
        if cart.lines and not replace_cart:
            current = await get_restaurant(session, cart.restaurant_id)
            name = current.name if current else "another restaurant"
            raise OtherRestaurant(f"Your cart has dishes from {name}.", name)
        cart.lines.clear()
        cart.restaurant_id = restaurant.id

    same = next((ln for ln in cart.lines if _same_choice(ln, new)), None)
    if same is not None:
        if same.quantity + new.quantity > MAX_QUANTITY:
            raise InvalidChoice(f"At most {MAX_QUANTITY} of one dish.")
        same.quantity += new.quantity
    else:
        cart.lines.append(
            CartLine(
                item_id=item.id,
                quantity=new.quantity,
                option_ids=config.option_ids,
                removed=config.removed,
            )
        )
    await session.flush()
    return await get_cart(session, user_id, constraints)


def _same_choice(line: CartLine, new: NewLine) -> bool:
    return (
        line.item_id == new.item_id
        and sorted(line.option_ids) == sorted(new.option_ids)
        and sorted(line.removed) == sorted(set(new.removed))
    )
