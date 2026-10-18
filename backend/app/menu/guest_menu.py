"""A restaurant's whole menu as one guest sees it, in the restaurant's category order."""

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.constraints import HardConstraints
from app.menu.guest_view import GuestItem, guest_item
from app.menu.queries import restaurant_by_slug, search_items
from app.menu.restaurant_schemas import RestaurantOut
from app.menu.schemas import MenuFilter, MenuItemOut
from app.menu.taste import NO_TASTES, Tastes


class GuestMenu(BaseModel):
    restaurant: RestaurantOut
    items: list[GuestItem]


async def guest_menu(
    session: AsyncSession, slug: str, constraints: HardConstraints, tastes: Tastes = NO_TASTES
) -> GuestMenu | None:
    """Every dish, including ones that do not suit the guest (they carry the reasons);
    None if there is no such restaurant."""
    restaurant = await restaurant_by_slug(session, slug)
    if restaurant is None:
        return None
    rows = await search_items(session, restaurant.id, MenuFilter())
    order = {category: n for n, category in enumerate(restaurant.categories)}
    items = sorted(
        (guest_item(MenuItemOut.model_validate(row), constraints, tastes) for row in rows),
        key=lambda item: (order.get(item.category, len(order)), item.price_sar, item.id),
    )
    return GuestMenu(restaurant=RestaurantOut.model_validate(restaurant), items=items)
