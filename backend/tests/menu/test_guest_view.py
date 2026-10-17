"""Traces from options reach the guest: on each option, and on the card when unavoidable."""

from app.agent.schemas import cards_for
from app.menu.allergens import Allergen
from app.menu.guest_view import guest_item
from tests.factories import guest, latte


def test_each_option_carries_its_own_trace_warning() -> None:
    options = guest_item(latte(), guest(Allergen.GLUTEN)).option_groups[0].options
    assert {o.name: o.may_contain_warnings for o in options} == {
        "Whole milk": [],
        "Oat milk": [Allergen.GLUTEN],
        "Almond milk": [],
    }


def test_a_trace_every_fitting_required_choice_carries_is_on_the_card() -> None:
    """Dairy and tree nut leave only oat milk, which may contain gluten."""
    strict = guest(Allergen.DAIRY, Allergen.TREE_NUT, Allergen.GLUTEN)
    assert strict.item_may_contain_warnings(latte()) == [Allergen.GLUTEN]
    [card] = cards_for([latte()], strict)
    assert card.may_contain_warnings == [Allergen.GLUTEN]


def test_an_avoidable_trace_is_not_on_the_card() -> None:
    assert guest(Allergen.GLUTEN).item_may_contain_warnings(latte()) == []


def test_item_level_conflicts_and_traces_are_filled() -> None:
    blocked = guest_item(latte(with_oat=False), guest(Allergen.DAIRY, Allergen.TREE_NUT))
    assert blocked.conflicts_with_guest == ["no milk choice fits"]
    strict = guest_item(latte(), guest(Allergen.DAIRY, Allergen.TREE_NUT, Allergen.GLUTEN))
    assert strict.conflicts_with_guest == []
    assert strict.may_contain_warnings == [Allergen.GLUTEN]
