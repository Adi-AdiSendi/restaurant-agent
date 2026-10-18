from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.preference import Preference
from app.memory.profile import tastes
from app.menu import clock
from app.menu.taste import NO_TASTES, Tastes, liked, mentions, taste_notes, today_pick
from app.orders.cart_add import add_line
from app.orders.checkout import place_order
from app.orders.orders import kcal_since
from app.orders.schemas import NewLine
from tests.conftest import make_user
from tests.factories import dish, guest
from tests.orders.helpers import dish as seeded_dish

BURGER = dish(
    name="Mushroom Burger",
    ingredients=["beef patty", "mushrooms", "pickles"],
    removable=["pickles"],
    is_vegetarian=False,
    is_vegan=False,
    price_sar=Decimal("48.00"),
    spice_level=2,
    kcal=900,
)


def test_word_matching_ignores_case_and_plurals() -> None:
    assert mentions("Garlic Mayo", "mayo") and mentions("onion", "Onions")
    assert not mentions("pine nuts", "pine nutmeg")


def test_each_soft_note() -> None:
    every = Tastes(
        dislikes=("mushroom", "pickles"),
        today_avoid=("meat",),
        weekday="friday",
        budget=Decimal("40"),
        max_spice=1,
        kcal_left=650,
        likes=("beef",),
    )
    assert taste_notes(BURGER, every) == [
        "has mushroom, which you dislike",
        "you avoid meat on Fridays",
        "over your 40 SAR budget",
        "spicier than you like",
        "more than the 650 kcal left today",
    ]
    assert liked(BURGER, every)
    assert taste_notes(BURGER, NO_TASTES) == [] and not liked(BURGER, NO_TASTES)


def test_the_profile_keeps_only_todays_day_rules_and_counts_the_goal_down() -> None:
    rows = [
        Preference(kind="day_dislike", value="friday: meat"),
        Preference(kind="day_dislike", value="monday: rice"),
        Preference(kind="day_like", value="friday: mushrooms"),
        Preference(kind="day_like", value="sunday: fish"),
        Preference(kind="calories", value="1800"),
        Preference(kind="spice", value="mild"),
    ]
    got = tastes(rows, "friday", kcal_today=1200)
    assert got.today_avoid == ("meat",) and got.kcal_left == 600 and got.max_spice == 1
    assert got.today_want == ("mushrooms",)
    assert today_pick(BURGER, got) and not today_pick(BURGER, tastes(rows, "sunday", 0))


async def test_todays_kcal_counts_only_this_guests_orders_today(seeded: AsyncSession) -> None:
    me, other = await make_user(seeded, "taste_me"), await make_user(seeded, "taste_other")
    item_id, options = await seeded_dish(seeded, "bean-and-bloom", "Latte")
    line = NewLine(item_id=item_id, quantity=2, option_ids=[options["Small"], options["Oat milk"]])
    for user in (me, other):
        await add_line(seeded, user, "bean-and-bloom", line, guest())
        await place_order(seeded, user, "pickup", guest())
    assert await kcal_since(seeded, me, clock.start_of_day()) == 2 * (150 + 20)
