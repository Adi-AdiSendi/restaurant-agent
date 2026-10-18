"""Run one cart write in a savepoint of the turn's transaction (ADR 0019).

A refused write rolls back only itself, so the turn goes on with the cart as it
was. A successful one is kept until the turn commits; a timed-out turn undoes it.
"""

from collections.abc import Awaitable, Callable

from app.orders.errors import OrderError
from app.tools.context import ToolContext
from app.tools.errors import ToolError
from app.tools.order_errors import order_tool_error


async def cart_write[T](context: ToolContext, write: Callable[[], Awaitable[T]]) -> T | ToolError:
    try:
        async with context.session.begin_nested():
            return await write()
    except OrderError as exc:
        return order_tool_error(exc)
