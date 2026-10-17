"""When an item with options fits a guest, and which options conflict."""

from app.menu.allergens import Allergen
from tests.factories import dish, group, guest, latte, opt


def test_a_required_group_with_one_fitting_choice_fits() -> None:
    assert guest(Allergen.DAIRY).item_violations(latte()) == []
    assert guest(Allergen.DAIRY, Allergen.TREE_NUT).item_violations(latte()) == []


def test_a_required_group_without_a_fitting_choice_blocks_the_item() -> None:
    no_oat = latte(with_oat=False)
    reasons = guest(Allergen.DAIRY, Allergen.TREE_NUT).item_violations(no_oat)
    assert reasons == ["no milk choice fits"]


def test_base_conflicts_come_first() -> None:
    item = latte(with_oat=False).model_copy(update={"allergens": [Allergen.SOY]})
    reasons = guest(Allergen.SOY, Allergen.DAIRY, Allergen.TREE_NUT).item_violations(item)
    assert reasons == ["soy", "no milk choice fits"]


def test_optional_groups_never_block() -> None:
    bacon = opt(5, "Bacon", is_vegetarian=False, is_vegan=False)
    item = dish(option_groups=[group(1, "Extras", 0, 2, bacon)])
    assert guest(vegetarian=True).item_violations(item) == []


def test_min_two_needs_two_fitting_choices() -> None:
    sides = group(1, "Sides", 2, 2, opt(5, "Fries"), opt(6, "Slaw", allergens=["egg"]))
    reasons = guest(Allergen.EGG).item_violations(dish(option_groups=[sides]))
    assert reasons == ["no sides choice fits"]


def test_option_conflicts_lists_only_conflicting_options() -> None:
    assert guest(Allergen.DAIRY, vegan=True).option_conflicts(latte()) == {
        101: ["dairy", "not vegan"],
        112: ["not vegan"],
    }
    assert guest().option_conflicts(latte()) == {}
