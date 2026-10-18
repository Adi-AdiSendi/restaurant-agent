"""propose_checkout: show the guest a checkout card. It never places an order (ADR 0019)."""

from app.orders.cart import get_cart
from app.orders.errors import EmptyCart, UnavailableLines
from app.tools.cart_results import NO_PARAMETERS, CheckoutProposal, check_no_arguments
from app.tools.context import ToolContext
from app.tools.errors import ToolError
from app.tools.order_errors import order_tool_error

NAME = "propose_checkout"

NOTE = (
    "A checkout card is shown under your reply. The guest chooses pickup or dine-in "
    "and places the order with its button. Never say the order is placed."
)

DESCRIPTION = """Show a checkout card for the guest's cart under your reply, when the \
guest wants to order, check out or pay. The guest places the order with the card's \
button; you cannot place it, and you must never say it is placed.
Input: {} (no arguments). Example: {}
An empty cart returns error_category "empty_cart"; lines no longer on the menu return \
"unavailable".
Do NOT use it just to show the cart (use view_cart)."""

PARAMETERS = NO_PARAMETERS


async def handle(arguments: str, context: ToolContext) -> CheckoutProposal | ToolError:
    if error := check_no_arguments(arguments):
        return error
    cart = await get_cart(context.session, context.user_id, context.constraints)
    if not cart.lines:
        return order_tool_error(EmptyCart("The cart is empty."))
    if any(line.problem for line in cart.lines):
        return order_tool_error(UnavailableLines("Some lines are no longer on the menu."))
    return CheckoutProposal(cart=cart, note=NOTE)
