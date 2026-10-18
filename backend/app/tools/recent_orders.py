"""recent_orders: the guest's last few orders, newest first, at any restaurant."""

from app.orders.orders import get_order, list_orders
from app.tools.cart_results import NO_PARAMETERS, RecentOrders, check_no_arguments
from app.tools.context import ToolContext
from app.tools.errors import ToolError

NAME = "recent_orders"
LIMIT = 3

DESCRIPTION = f"""The guest's last {LIMIT} orders, newest first, at any restaurant: \
each with its restaurant, dishes (names, options, left-out ingredients), quantities, \
prices, status and time.
Use it when the guest asks about past orders or wants "the same as last time".
Input: {{}} (no arguments). Example: {{}}
Order lines have names, not menu IDs: to order one again here, find the dish with \
search_menu first. Dishes from another restaurant cannot be added here.
Do NOT use it for the current cart (it is in your context)."""

PARAMETERS = NO_PARAMETERS


async def handle(arguments: str, context: ToolContext) -> RecentOrders | ToolError:
    if error := check_no_arguments(arguments):
        return error
    summaries = (await list_orders(context.session, context.user_id))[:LIMIT]
    orders = [await get_order(context.session, context.user_id, o.id) for o in summaries]
    return RecentOrders(orders=orders)
