"""Turn the model's recommended IDs into database cards it actually saw."""

import logging
from collections.abc import Iterable

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.queries import get_items_by_ids
from app.menu.schemas import MenuItemOut
from app.tools.get_item import GetItemResult
from app.tools.search_menu import SearchMenuResult
from app.tools.show_menu import ShowMenuResult

logger = logging.getLogger(__name__)


def ids_in_tool_result(result: BaseModel) -> set[int]:
    if isinstance(result, SearchMenuResult | ShowMenuResult):
        return {item.id for item in result.items}
    if isinstance(result, GetItemResult):
        return {result.item.id}
    return set()


async def grounded_items(
    session: AsyncSession, restaurant_id: int, recommended: Iterable[int], seen: set[int]
) -> list[MenuItemOut]:
    """Keep IDs of this restaurant that were seen (a tool returned them this turn, or
    they were recommended earlier in this conversation); log and drop the rest."""
    allowed: list[int] = []
    for item_id in recommended:
        if item_id in seen:
            allowed.append(item_id)
        else:
            logger.warning("agent_unseen_item_id id=%d", item_id)
    found = await get_items_by_ids(session, restaurant_id, allowed)
    known = {item.id for item in found}
    for item_id in allowed:
        if item_id not in known:
            logger.warning("agent_unknown_item_id id=%d", item_id)
    return [MenuItemOut.model_validate(item) for item in found]
