"""Every item in every restaurant, against every allergen and diet.

The fit rule (`item_violations`) must agree with a brute force over the
resolver: an item is allowed exactly when some valid way of ordering it is safe.
"""

from collections.abc import Iterator
from itertools import combinations, product

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.allergens import Allergen
from app.menu.configure import configure
from app.menu.constraints import HardConstraints
from app.menu.models import MenuItem
from app.menu.schemas import MenuItemOut
from app.safety.guard import check
from tests.factories import guest

GUESTS = [guest(a) for a in Allergen] + [guest(vegetarian=True), guest(vegan=True)]
NAMES = [a.value for a in Allergen] + ["vegetarian", "vegan"]
MAX_CONFIGURATIONS = 5000


def choice_sets(item: MenuItemOut) -> Iterator[list[int]]:
    per_group = [
        [
            list(chosen)
            for n in range(group.min_choices, group.max_choices + 1)
            for chosen in combinations([o.id for o in group.options], n)
        ]
        for group in item.option_groups
    ]
    for picks in product(*per_group):
        yield [option_id for pick in picks for option_id in pick]


async def all_items(session: AsyncSession) -> list[MenuItemOut]:
    rows = await session.scalars(select(MenuItem).order_by(MenuItem.id))
    return [MenuItemOut.model_validate(row) for row in rows]


@pytest.mark.parametrize("constraints", GUESTS, ids=NAMES)
async def test_fit_rule_matches_brute_force(
    seeded: AsyncSession, constraints: HardConstraints
) -> None:
    menu = await all_items(seeded)
    allowed = {item.id for item in check(menu, constraints).allowed}
    assert allowed, "every guest must be able to order something"
    for item in menu:
        configs = list(choice_sets(item))
        assert len(configs) <= MAX_CONFIGURATIONS, item.name
        some_safe = any(not constraints.violations(configure(item, ids, [])) for ids in configs)
        assert (item.id in allowed) == some_safe, item.name


async def test_a_base_diet_flag_is_reachable(seeded: AsyncSession) -> None:
    """A dish flagged vegetarian or vegan can be ordered that way: no required group
    forces meat (or dairy) on it, so its badge and the SQL diet filter are honest."""
    for item in await all_items(seeded):
        if item.is_vegan:
            assert not guest(vegan=True).item_violations(item), item.name
        if item.is_vegetarian:
            assert not guest(vegetarian=True).item_violations(item), item.name
