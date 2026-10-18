"""Tool specs for the model and dispatch from a tool call to its handler."""

from collections.abc import Awaitable, Callable

from pydantic import BaseModel

from app.agent.llm_client import Spec, ToolCall
from app.tools import (
    add_to_cart,
    get_item,
    propose_checkout,
    recent_orders,
    remove_cart_line,
    search_menu,
    update_cart_line,
    view_cart,
)
from app.tools.context import ToolContext
from app.tools.errors import ToolError

# Handlers get the user, restaurant and constraints from the server (ADR 0020),
# never from the model's arguments.
Handler = Callable[[str, ToolContext], Awaitable[BaseModel]]

_TOOLS = (
    search_menu,
    get_item,
    view_cart,
    add_to_cart,
    update_cart_line,
    remove_cart_line,
    recent_orders,
    propose_checkout,
)
HANDLERS: dict[str, Handler] = {tool.NAME: tool.handle for tool in _TOOLS}
TOOL_SPECS: list[Spec] = [
    {
        "type": "function",
        "name": tool.NAME,
        "description": tool.DESCRIPTION,
        "parameters": tool.PARAMETERS,
        "strict": True,
    }
    for tool in _TOOLS
]


async def run_tool(call: ToolCall, context: ToolContext) -> BaseModel:
    handler = HANDLERS.get(call.name)
    if handler is None:
        return ToolError(
            error_category="unknown_tool",
            retryable=False,
            message=f"There is no tool named {call.name!r}. Use one of: {sorted(HANDLERS)}.",
        )
    return await handler(call.arguments, context)
