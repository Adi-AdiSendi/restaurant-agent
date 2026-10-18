"""Estimated calories: in the data, through configure, in the cart and on orders."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.configure import configure
from app.orders.cart_add import add_line
from app.orders.checkout import place_order
from app.orders.schemas import NewLine
from scripts.seed_menu import load_restaurants
from tests.conftest import make_user
from tests.factories import dish, group, guest, opt
from tests.orders.helpers import dish as seeded_dish


def test_every_dish_has_an_estimate() -> None:
    missing = [
        f"{r.slug}/{i.name}" for r in load_restaurants() for i in r.items if i.kcal is None
    ]
    assert not missing


def test_options_add_or_save_kcal_and_never_go_below_zero() -> None:
    sizes = group(7, "Size", 1, 1, opt(71, "Small"), opt(72, "Large", kcal_delta=130))
    cheese, wrap = opt(81, "Cheese", kcal_delta=110), opt(82, "Wrap", kcal_delta=-900)
    extras = group(8, "Extras", 0, 2, cheese, wrap)
    item = dish(kcal=500, option_groups=[sizes, extras])
    assert configure(item, [72, 81], []).kcal == 740
    assert configure(item, [71, 82], []).kcal == 0
    assert configure(dish(option_groups=[]), [], []).kcal is None


async def test_the_cart_and_the_order_carry_kcal(seeded: AsyncSession) -> None:
    user = await make_user(seeded, "kcal_cart")
    item_id, options = await seeded_dish(seeded, "bean-and-bloom", "Latte")
    line = NewLine(item_id=item_id, quantity=2, option_ids=[options["Large"], options["Oat milk"]])
    cart = await add_line(seeded, user, "bean-and-bloom", line, guest())
    one = 150 + 130 + 20  # latte, large, oat milk
    assert cart.lines[0].kcal == one and cart.kcal == 2 * one
    order = await place_order(seeded, user, "pickup", guest())
    assert order.lines[0].kcal == one
