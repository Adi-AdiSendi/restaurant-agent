"""Shared helpers for the cart tool tests: a user's context and calls by tool module."""

import json
from types import ModuleType

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.constraints import NO_CONSTRAINTS, HardConstraints
from app.tools.context import ToolContext
from tests.contexts import tool_context
from tests.orders.helpers import dish

CAFE = "bean-and-bloom"
BURGERS = "stack-and-smash"


async def guest_context(
    session: AsyncSession,
    user_id: int,
    slug: str = CAFE,
    constraints: HardConstraints = NO_CONSTRAINTS,
    dislikes: tuple[str, ...] = (),
) -> ToolContext:
    return await tool_context(session, constraints, slug, user_id=user_id, dislikes=dislikes)


async def call(tool: ModuleType, context: ToolContext, **arguments: object) -> BaseModel:
    result: BaseModel = await tool.handle(json.dumps(arguments), context)
    return result


async def latte_args(
    session: AsyncSession, milk: str = "Oat milk", quantity: int = 1
) -> dict[str, object]:
    item_id, options = await dish(session, CAFE, "Latte")
    return {
        "item_id": item_id,
        "quantity": quantity,
        "option_ids": [options["Small"], options[milk]],
        "removed": [],
        "keep_ingredients": [],
    }


async def smash_args(session: AsyncSession, keep: list[str] | None = None) -> dict[str, object]:
    item_id, options = await dish(session, BURGERS, "Classic Smash")
    return {
        "item_id": item_id,
        "quantity": 1,
        "option_ids": [options["Single patty"], options["Brioche bun"]],
        "removed": [],
        "keep_ingredients": keep or [],
    }
