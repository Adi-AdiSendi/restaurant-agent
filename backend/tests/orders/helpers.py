"""Find real dishes and options by name, for cart and checkout tests."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.models import MenuItem, Option, OptionGroup
from app.menu.restaurant import Restaurant


async def dish(session: AsyncSession, slug: str, name: str) -> tuple[int, dict[str, int]]:
    """The item's ID and its option IDs by option name."""
    item_id = (
        await session.scalars(
            select(MenuItem.id)
            .join(Restaurant, Restaurant.id == MenuItem.restaurant_id)
            .where(Restaurant.slug == slug, MenuItem.name == name)
        )
    ).one()
    rows = await session.execute(
        select(Option.name, Option.id).join(OptionGroup).where(OptionGroup.item_id == item_id)
    )
    return item_id, {option_name: option_id for option_name, option_id in rows.all()}
