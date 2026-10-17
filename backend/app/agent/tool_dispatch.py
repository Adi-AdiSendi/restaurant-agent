"""Tool specs for the model and dispatch from a tool call to its handler."""

from collections.abc import Awaitable, Callable

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.llm_client import Spec, ToolCall
from app.menu.constraints import HardConstraints
from app.tools import get_item, search_menu
from app.tools.errors import ToolError

# Handlers get the guest's constraints from the server, never a user_id.
Handler = Callable[[AsyncSession, str, HardConstraints], Awaitable[BaseModel]]

_TOOLS = (search_menu, get_item)
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


async def run_tool(
    session: AsyncSession, call: ToolCall, constraints: HardConstraints
) -> BaseModel:
    handler = HANDLERS.get(call.name)
    if handler is None:
        return ToolError(
            error_category="unknown_tool",
            retryable=False,
            message=f"There is no tool named {call.name!r}. Use one of: {sorted(HANDLERS)}.",
        )
    return await handler(session, call.arguments, constraints)
