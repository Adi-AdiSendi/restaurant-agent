"""Make the menu tables match data/restaurants/*.json. Safe to run on every deploy.

Usage: uv run python -m scripts.seed_menu
"""

import asyncio
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_engine, get_sessionmaker
from app.menu.restaurant import Restaurant
from app.menu.restaurant_schemas import RestaurantFile
from scripts.menu_sync import sync_restaurant

RESTAURANTS_DIR = Path(__file__).resolve().parents[1] / "data" / "restaurants"
logger = logging.getLogger(__name__)


def load_restaurants(directory: Path = RESTAURANTS_DIR) -> list[RestaurantFile]:
    """Every restaurant file, Corner Table first, the rest by name."""
    paths = sorted(directory.glob("*.json"), key=lambda p: (p.stem != "corner-table", p.stem))
    if not paths:
        raise ValueError(f"{directory} has no restaurant files")
    restaurants = [RestaurantFile.model_validate_json(p.read_bytes()) for p in paths]
    for path, restaurant in zip(paths, restaurants, strict=True):
        if restaurant.slug != path.stem:
            raise ValueError(f"{path.name}: slug {restaurant.slug!r} must match the file name")
    return restaurants


async def seed_menus(session: AsyncSession, restaurants: list[RestaurantFile]) -> None:
    """Restaurants missing from the files are kept, since conversations point at them;
    only their absence is logged."""
    for position, restaurant in enumerate(restaurants):
        await sync_restaurant(session, restaurant, position)
    known = {r.slug for r in restaurants}
    for slug in await session.scalars(select(Restaurant.slug)):
        if slug not in known:
            logger.warning("restaurant_not_in_files slug=%s", slug)


async def main() -> None:
    restaurants = load_restaurants()
    async with get_sessionmaker()() as session, session.begin():
        await seed_menus(session, restaurants)
    await get_engine().dispose()
    items = sum(len(r.items) for r in restaurants)
    logger.info("menu_seeded restaurants=%d items=%d", len(restaurants), items)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    asyncio.run(main())
