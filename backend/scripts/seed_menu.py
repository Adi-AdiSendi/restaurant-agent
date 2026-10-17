"""Make menu_items match data/menu.json. Safe to run on every deploy.

Usage: uv run python -m scripts.seed_menu
"""

import asyncio
import logging
from pathlib import Path

from pydantic import TypeAdapter
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_engine, get_sessionmaker
from app.menu.models import MenuItem
from app.menu.schemas import MenuItemFields

MENU_PATH = Path(__file__).resolve().parents[1] / "data" / "menu.json"
logger = logging.getLogger(__name__)

_menu_adapter = TypeAdapter(list[MenuItemFields])


def load_menu(path: Path = MENU_PATH) -> list[MenuItemFields]:
    items = _menu_adapter.validate_json(path.read_bytes())
    if not items:
        raise ValueError(f"{path} has no menu items")
    return items


async def seed_menu(session: AsyncSession, items: list[MenuItemFields]) -> None:
    """Upsert by name, then delete rows the file no longer lists.

    The file is the source of truth: a removed or renamed dish must not stay
    recommendable. Keeping names stable keeps IDs stable.
    """
    rows = [item.model_dump() for item in items]
    stmt = insert(MenuItem).values(rows)
    updatable = {c: stmt.excluded[c] for c in rows[0] if c != "name"}
    await session.execute(stmt.on_conflict_do_update(index_elements=["name"], set_=updatable))
    names = [item.name for item in items]
    await session.execute(delete(MenuItem).where(MenuItem.name.not_in(names)))


async def main() -> None:
    items = load_menu()
    async with get_sessionmaker()() as session, session.begin():
        await seed_menu(session, items)
    await get_engine().dispose()
    logger.info("menu_seeded items=%d", len(items))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    asyncio.run(main())
