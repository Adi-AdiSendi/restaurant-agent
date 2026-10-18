"""clear_cart: empty the guest's cart, when they ask or agree (ADR 0019, amended)."""

from app.orders.cart import get_cart
from app.orders.cart_edit import clear_cart
from app.tools.cart_results import NO_PARAMETERS, CartChange, check_no_arguments
from app.tools.cart_write import cart_write
from app.tools.context import ToolContext
from app.tools.errors import ToolError

NAME = "clear_cart"

DESCRIPTION = """Empty the guest's whole cart, at any restaurant.
Use it only when the guest asks ("empty my cart", "start over", "order me X instead") \
or agrees after you asked, for example to replace a cart from another restaurant \
before adding what they want here. Then add the new dishes with add_to_cart.
Input: {} (no arguments). Example: {}
Do NOT use it on your own initiative, or to remove one dish (use remove_cart_line). \
It never places an order."""

PARAMETERS = NO_PARAMETERS


async def handle(arguments: str, context: ToolContext) -> CartChange | ToolError:
    if error := check_no_arguments(arguments):
        return error
    before = await get_cart(context.session, context.user_id, context.constraints)
    cart = await cart_write(context, lambda: clear_cart(context.session, context.user_id))
    if isinstance(cart, ToolError):
        return cart
    return CartChange(action="cleared", quantity=before.item_count, line=None, cart=cart)
