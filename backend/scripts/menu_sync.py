"""Make one restaurant's rows match its file: upsert by name, delete what the file dropped.

Each level is keyed by its parent and name: restaurants by slug, items by
(restaurant, name), groups by (item, name), options by (group, name). Stable
names keep IDs stable. Deletes stay inside this restaurant's rows.
"""

from collections.abc import Sequence
from typing import Any, cast

from sqlalchemy import ColumnElement, Result, delete, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.dml import ReturningInsert

from app.menu.models import MenuItem, Option, OptionGroup
from app.menu.restaurant import Restaurant
from app.menu.restaurant_schemas import RestaurantFile

# Row values are column -> value dicts for a bulk insert; their types vary by column.
Row = dict[str, Any]
Model = type[Restaurant | MenuItem | OptionGroup | Option]


async def _upsert(
    session: AsyncSession,
    model: Model,
    rows: Sequence[Row],
    keys: Sequence[str],
) -> dict[tuple[object, ...], int]:
    """Insert or update `rows`; returns their IDs by key."""
    if not rows:
        return {}
    stmt = insert(model).values(list(rows))
    updates = {c: stmt.excluded[c] for c in rows[0] if c not in keys}
    key_columns: list[InstrumentedAttribute[Any]] = [getattr(model, k) for k in keys]
    stmt = stmt.on_conflict_do_update(index_elements=list(keys), set_=updates)
    # pyright cannot type insert() over a union of models; the columns are known here.
    returning = cast("ReturningInsert[Any]", stmt.returning(model.id, *key_columns))
    result: Result[Any] = await session.execute(returning)
    return {tuple(row[1:]): int(row[0]) for row in result}


async def _delete_missing(
    session: AsyncSession,
    model: Model,
    parent: InstrumentedAttribute[int],
    parent_ids: Sequence[int],
    keep: ColumnElement[bool],
) -> None:
    await session.execute(delete(model).where(parent.in_(parent_ids), ~keep))


async def sync_restaurant(session: AsyncSession, data: RestaurantFile, position: int) -> int:
    """Returns the restaurant's ID."""
    fields = data.model_dump(exclude={"items"}) | {"position": position}
    rid = (await _upsert(session, Restaurant, [fields], ["slug"]))[(data.slug,)]

    items = [
        item.model_dump(exclude={"option_groups"}) | {"restaurant_id": rid} for item in data.items
    ]
    item_ids = await _upsert(session, MenuItem, items, ["restaurant_id", "name"])
    names = [item.name for item in data.items]
    await _delete_missing(
        session, MenuItem, MenuItem.restaurant_id, [rid], MenuItem.name.in_(names)
    )

    groups: list[Row] = []
    for item in data.items:
        item_id = item_ids[(rid, item.name)]
        groups += [
            group.model_dump(exclude={"options"}) | {"item_id": item_id, "position": n}
            for n, group in enumerate(item.option_groups)
        ]
    group_ids = await _upsert(session, OptionGroup, groups, ["item_id", "name"])
    kept = tuple_(OptionGroup.item_id, OptionGroup.name).in_(list(group_ids))
    await _delete_missing(session, OptionGroup, OptionGroup.item_id, list(item_ids.values()), kept)

    options: list[Row] = []
    for item in data.items:
        for group in item.option_groups:
            group_id = group_ids[(item_ids[(rid, item.name)], group.name)]
            options += [
                option.model_dump() | {"group_id": group_id, "position": n}
                for n, option in enumerate(group.options)
            ]
    option_ids = await _upsert(session, Option, options, ["group_id", "name"])
    kept = tuple_(Option.group_id, Option.name).in_(list(option_ids))
    await _delete_missing(session, Option, Option.group_id, list(group_ids.values()), kept)
    return rid
