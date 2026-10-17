"""Every branch of the hard-constraint rule and the post-check. The exhaustive
pass over every real menu is in test_guard_exhaustive.py."""

import pytest

from app.menu.allergens import Allergen
from app.menu.constraints import NO_CONSTRAINTS, HardConstraints
from app.menu.schemas import MenuItemOut
from app.safety.guard import check
from tests.factories import dish, guest, latte


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


def test_an_option_can_block_an_item() -> None:
    no_oat = latte(with_oat=False)
    result = check([no_oat, latte()], guest(Allergen.DAIRY, Allergen.TREE_NUT))
    assert [b.reasons for b in result.blocked] == [["no milk choice fits"]]
    assert [i.name for i in result.allowed] == ["Latte"]
