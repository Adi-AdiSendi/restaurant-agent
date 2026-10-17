"""Corner Table helpers for DB tests: its ID, a scoped search, and a tool context."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.constraints import NO_CONSTRAINTS, HardConstraints
from app.menu.models import MenuItem
from app.menu.queries import search_items
from app.menu.restaurant import Restaurant
from app.menu.schemas import MenuFilter
from app.tools.context import ToolContext


async def restaurant_row(session: AsyncSession, slug: str = "corner-table") -> Restaurant:
    return (await session.scalars(select(Restaurant).where(Restaurant.slug == slug))).one()


async def corner_items(
    session: AsyncSession, menu_filter: MenuFilter | None = None
) -> Sequence[MenuItem]:
    restaurant = await restaurant_row(session)
    return await search_items(session, restaurant.id, menu_filter or MenuFilter())


async def tool_context(
    session: AsyncSession,
    constraints: HardConstraints = NO_CONSTRAINTS,
    slug: str = "corner-table",
) -> ToolContext:
    """User and conversation IDs are placeholders: menu tools never read them."""
    restaurant = await restaurant_row(session, slug)
    categories = tuple(restaurant.categories)
    return ToolContext(session, 0, 0, restaurant.id, categories, constraints)
