"""Every branch of the hard-constraint rule and the post-check, plus an
exhaustive pass over the real menu for every allergen and diet."""

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.menu.allergens import Allergen
from app.menu.constraints import NO_CONSTRAINTS, HardConstraints
from app.menu.queries import search_items
from app.menu.schemas import MenuFilter, MenuItemOut
from app.safety.guard import check


def dish(**override: object) -> MenuItemOut:
    fields: dict[str, object] = {
        "id": 1,
        "name": "Dish",
        "category": "starters",
        "description": "d",
        "price_sar": Decimal("10.00"),
        "is_vegetarian": True,
        "is_vegan": True,
        "spice_level": 0,
        "ingredients": ["x"],
        "allergens": [],
        "may_contain": [],
    }
    return MenuItemOut.model_validate(fields | override)


def guest(*allergens: Allergen, vegetarian: bool = False, vegan: bool = False) -> HardConstraints:
    return HardConstraints(
        excluded_allergens=frozenset(allergens), vegetarian=vegetarian, vegan=vegan
    )


@pytest.mark.parametrize(
    ("item", "constraints", "reasons"),
    [
        (dish(allergens=["peanut", "soy"]), guest(Allergen.PEANUT), ["peanut"]),
        (
            dish(allergens=["peanut", "soy"]),
            guest(Allergen.SOY, Allergen.PEANUT),
            ["peanut", "soy"],
        ),
        (dish(allergens=["dairy"]), guest(Allergen.PEANUT), []),
        (dish(is_vegan=False), guest(vegan=True), ["not vegan"]),
        (dish(is_vegan=False, is_vegetarian=False), guest(vegan=True), ["not vegan"]),
        (dish(is_vegan=False, is_vegetarian=False), guest(vegetarian=True), ["not vegetarian"]),
        (dish(is_vegan=False), guest(vegetarian=True), []),
        (dish(may_contain=["tree_nut"]), guest(Allergen.TREE_NUT), []),
        (
            dish(allergens=["egg"], is_vegan=False),
            guest(Allergen.EGG, vegan=True),
            ["egg", "not vegan"],
        ),
        (dish(allergens=["fish"], is_vegetarian=False, is_vegan=False), NO_CONSTRAINTS, []),
    ],
)
def test_violations(item: MenuItemOut, constraints: HardConstraints, reasons: list[str]) -> None:
    assert constraints.violations(item) == reasons


def test_may_contain_gives_a_warning_only_for_avoided_allergens() -> None:
    item = dish(may_contain=["tree_nut", "sesame"])
    assert guest(Allergen.TREE_NUT).may_contain_warnings(item) == [Allergen.TREE_NUT]
    assert guest(Allergen.PEANUT).may_contain_warnings(item) == []


def test_check_splits_allowed_and_blocked() -> None:
    safe, nutty = dish(id=1), dish(id=2, name="Nutty", allergens=["peanut"])
    result = check([safe, nutty], guest(Allergen.PEANUT))
    assert [i.id for i in result.allowed] == [1]
    assert [(b.item_id, b.name, b.reasons) for b in result.blocked] == [(2, "Nutty", ["peanut"])]


def test_no_constraints_allow_everything() -> None:
    items = [dish(id=1, allergens=["peanut"]), dish(id=2, is_vegan=False, is_vegetarian=False)]
    assert check(items, NO_CONSTRAINTS).blocked == []


@pytest.mark.parametrize("allergen", list(Allergen))
async def test_every_menu_item_against_every_allergen(
    seeded: AsyncSession, allergen: Allergen
) -> None:
    menu = [MenuItemOut.model_validate(row) for row in await search_items(seeded, MenuFilter())]
    result = check(menu, guest(allergen))
    assert {b.item_id for b in result.blocked} == {i.id for i in menu if allergen in i.allergens}
    assert all(allergen not in i.allergens for i in result.allowed)


@pytest.mark.parametrize(
    ("constraints", "flag"),
    [(guest(vegan=True), "is_vegan"), (guest(vegetarian=True), "is_vegetarian")],
)
async def test_every_menu_item_against_each_diet(
    seeded: AsyncSession, constraints: HardConstraints, flag: str
) -> None:
    menu = [MenuItemOut.model_validate(row) for row in await search_items(seeded, MenuFilter())]
    result = check(menu, constraints)
    assert result.allowed
    assert all(getattr(i, flag) for i in result.allowed)
    assert {b.item_id for b in result.blocked} == {i.id for i in menu if not getattr(i, flag)}
