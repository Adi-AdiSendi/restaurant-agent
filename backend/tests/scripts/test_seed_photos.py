import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.models import MenuItem
from app.menu.restaurant import Restaurant
from scripts.menu_sync import sync_restaurant
from scripts.seed_menu import load_restaurants

CORNER_TABLE = load_restaurants()[0]


async def test_the_seed_stores_dish_and_cover_photos(session: AsyncSession) -> None:
    first = CORNER_TABLE.items[0]
    with_photos = CORNER_TABLE.model_copy(
        update={
            "photo": "corner-table/cover",
            "items": [
                first.model_copy(update={"photo": "corner-table/fries"}),
                CORNER_TABLE.items[1].model_copy(update={"photo": None}),
                *CORNER_TABLE.items[2:],
            ],
        }
    )
    rid = await sync_restaurant(session, with_photos, 0)
    session.expire_all()
    restaurant = await session.get(Restaurant, rid)
    assert restaurant is not None and restaurant.photo == "corner-table/cover"
    rows = await session.execute(
        select(MenuItem.name, MenuItem.photo).where(MenuItem.restaurant_id == rid)
    )
    photos = {name: photo for name, photo in rows}
    assert photos[first.name] == "corner-table/fries"
    assert photos[CORNER_TABLE.items[1].name] is None


@pytest.mark.parametrize("photo", ["fries", "corner-table/../secret", "Corner/Fries", "a/b/c"])
def test_a_photo_must_be_restaurant_slash_name(photo: str) -> None:
    with pytest.raises(ValidationError):
        CORNER_TABLE.items[0].model_validate(CORNER_TABLE.items[0].model_dump() | {"photo": photo})
