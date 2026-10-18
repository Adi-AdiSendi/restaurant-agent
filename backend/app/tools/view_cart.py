"""view_cart: the guest's cart as the server prices it now."""

from app.orders.cart import get_cart
from app.tools.cart_results import NO_PARAMETERS, CartView, check_no_arguments
from app.tools.context import ToolContext
from app.tools.errors import ToolError

NAME = "view_cart"

DESCRIPTION = """Show the guest's cart: each line's id, dish, options, left-out \
ingredients, quantity and price, the total, and the restaurant it is from.
Use it when the guest asks what is in their cart or what it costs. The cart as it \
was at the start of this turn is already in your context.
Input: {} (no arguments). Example: {}
Do NOT use it to change the cart; use add_to_cart, update_cart_line or remove_cart_line."""

PARAMETERS = NO_PARAMETERS


async def handle(arguments: str, context: ToolContext) -> CartView | ToolError:
    if error := check_no_arguments(arguments):
        return error
    return CartView(cart=await get_cart(context.session, context.user_id, context.constraints))
