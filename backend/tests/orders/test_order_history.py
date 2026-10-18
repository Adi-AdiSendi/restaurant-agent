from sqlalchemy.ext.asyncio import AsyncSession

from app.orders.cart_add import add_line
from app.orders.checkout import place_order
from app.orders.orders import get_order, list_orders
from app.orders.schemas import NewLine
from tests.conftest import make_user
from tests.factories import guest
from tests.orders.helpers import dish


async def test_history_shows_dish_photos_and_estimated_kcal(seeded: AsyncSession) -> None:
    user = await make_user(seeded, "history_user")
    latte_id, options = await dish(seeded, "bean-and-bloom", "Latte")
    dates_id, _ = await dish(seeded, "bean-and-bloom", "Khalas Dates (box of 3)")
    latte = NewLine(item_id=latte_id, option_ids=[options["Small"], options["Oat milk"]])
    await add_line(seeded, user, "bean-and-bloom", latte, guest())
    await add_line(seeded, user, "bean-and-bloom", NewLine(item_id=dates_id, quantity=2), guest())
    placed = await place_order(seeded, user, "pickup", guest())

    [summary] = await list_orders(seeded, user)
    assert summary.photos == ["bean-and-bloom/latte"]  # the dates have no photo
    assert summary.kcal == (150 + 20) + 2 * 70
    order = await get_order(seeded, user, placed.id)
    assert [line.photo for line in order.lines] == ["bean-and-bloom/latte", None]
