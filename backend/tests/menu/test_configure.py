"""Every branch of the resolver: prices, limits, allergens and diet added by options."""

from decimal import Decimal

import pytest

from app.menu.allergens import Allergen
from app.menu.configure import ConfigurationError, configure
from tests.factories import latte


def test_base_with_required_choice() -> None:
    config = configure(latte(), [102], [])
    assert config.unit_price_sar == Decimal("17.00")
    assert config.allergens == []
    assert config.may_contain == [Allergen.GLUTEN]
    assert config.is_vegan and config.is_vegetarian
    assert config.spice_level == 0


def test_options_add_price_allergens_diet_and_spice() -> None:
    config = configure(latte(), [101, 111, 113], [])
    assert config.unit_price_sar == Decimal("16.00")
    assert config.allergens == [Allergen.DAIRY]
    assert not config.is_vegan
    assert config.is_vegetarian
    assert config.spice_level == 2


def test_a_contained_allergen_is_not_also_a_trace() -> None:
    item = latte().model_copy(update={"may_contain": [Allergen.DAIRY]})
    assert configure(item, [101], []).may_contain == []


def test_removal_is_kept_and_never_clears_an_allergen() -> None:
    item = latte().model_copy(update={"allergens": [Allergen.SESAME]})
    config = configure(item, [102], ["sugar", "sugar"])
    assert config.removed == ["sugar"]
    assert config.allergens == [Allergen.SESAME]


@pytest.mark.parametrize(
    ("option_ids", "removed", "message"),
    [
        ([], [], "at least 1 Milk"),
        ([101, 102], [], "at most 1 Milk"),
        ([102, 111, 112, 113], [], "at most 2 Syrup"),
        ([102, 102], [], "more than once"),
        ([102, 999], [], r"\[999\] are not offered"),
        ([102], ["espresso"], "cannot be left out"),
    ],
)
def test_invalid_choices_are_rejected(
    option_ids: list[int], removed: list[str], message: str
) -> None:
    with pytest.raises(ConfigurationError, match=message):
        configure(latte(), option_ids, removed)
