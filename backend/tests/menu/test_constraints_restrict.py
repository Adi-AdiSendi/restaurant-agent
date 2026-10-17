"""HardConstraints.restrict can only narrow the model's filter, never widen it."""

from decimal import Decimal

from app.menu.allergens import Allergen
from app.menu.categories import Category
from app.menu.constraints import NO_CONSTRAINTS, HardConstraints
from app.menu.schemas import MenuFilter


def test_guest_constraints_are_added_to_an_empty_model_filter() -> None:
    guest = HardConstraints(excluded_allergens=frozenset({Allergen.PEANUT}), vegan=True)
    merged = guest.restrict(MenuFilter())
    assert merged.exclude_allergens == [Allergen.PEANUT]
    assert merged.vegan
    assert merged.vegetarian


def test_model_choices_are_kept_and_combined() -> None:
    guest = HardConstraints(excluded_allergens=frozenset({Allergen.PEANUT}))
    model = MenuFilter(
        category=Category.STARTERS,
        max_price_sar=Decimal("30"),
        exclude_allergens=[Allergen.DAIRY],
        vegetarian=True,
    )
    merged = guest.restrict(model)
    assert merged.exclude_allergens == [Allergen.DAIRY, Allergen.PEANUT]
    assert merged.category == Category.STARTERS
    assert merged.max_price_sar == Decimal("30")
    assert merged.vegetarian


def test_the_model_cannot_switch_a_diet_off() -> None:
    merged = HardConstraints(vegetarian=True).restrict(MenuFilter(vegetarian=False, vegan=False))
    assert merged.vegetarian


def test_no_constraints_leave_the_filter_unchanged() -> None:
    model = MenuFilter(max_spice=1, text="bowl")
    assert NO_CONSTRAINTS.restrict(model) == model
