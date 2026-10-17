"""Menu reads. All filtering happens in SQL, before any item reaches the model."""

from collections.abc import Sequence

from sqlalchemy import Select, func, not_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.models import MenuItem
from app.menu.schemas import MenuFilter


def _apply_filter(stmt: Select[MenuItem], f: MenuFilter) -> Select[MenuItem]:
    if f.category is not None:
        stmt = stmt.where(MenuItem.category == f.category.value)
    if f.max_price_sar is not None:
        stmt = stmt.where(MenuItem.price_sar <= f.max_price_sar)
    if f.max_spice is not None:
        stmt = stmt.where(MenuItem.spice_level <= f.max_spice)
    if f.vegetarian:
        stmt = stmt.where(MenuItem.is_vegetarian)
    if f.vegan:
        stmt = stmt.where(MenuItem.is_vegan)
    if f.exclude_allergens:
        stmt = stmt.where(not_(MenuItem.allergens.overlap([a.value for a in f.exclude_allergens])))
    if f.text:
        escaped = f.text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        searchable = func.concat_ws(
            " ",
            MenuItem.name,
            MenuItem.description,
            func.replace(MenuItem.category, "_", " "),
            func.array_to_string(MenuItem.ingredients, " "),
        )
        stmt = stmt.where(searchable.ilike(f"%{escaped}%", escape="\\"))
    return stmt


async def search_items(session: AsyncSession, menu_filter: MenuFilter) -> Sequence[MenuItem]:
    stmt = _apply_filter(select(MenuItem), menu_filter).order_by(MenuItem.price_sar, MenuItem.id)
    return (await session.scalars(stmt)).all()


async def get_item(session: AsyncSession, item_id: int) -> MenuItem | None:
    return await session.get(MenuItem, item_id)


async def get_items_by_ids(session: AsyncSession, item_ids: Sequence[int]) -> Sequence[MenuItem]:
    """Unknown IDs are dropped. Results keep the order of `item_ids`."""
    if not item_ids:
        return []
    found = await session.scalars(select(MenuItem).where(MenuItem.id.in_(item_ids)))
    by_id = {item.id: item for item in found}
    return [by_id[i] for i in dict.fromkeys(item_ids) if i in by_id]
