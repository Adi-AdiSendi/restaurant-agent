from decimal import Decimal
from typing import Any

import pytest

from app.agent.schemas import Card
from evals.case_model import Expect, ProfileExpect
from evals.graders.cards import grade_turn
from evals.graders.memory import grade_profile
from evals.graders.prices import grade_prices, prices_by_restaurant, stated_prices
from evals.transcript import StoredFact, Turn
from scripts.seed_menu import load_restaurants


def card(name: str, **fields: Any) -> Card:
    base: dict[str, Any] = {
        "id": 1,
        "name": name,
        "category": "desserts_and_drinks",
        "description": "d",
        "price_sar": Decimal("20.00"),
        "is_vegetarian": True,
        "is_vegan": True,
        "spice_level": 0,
        "ingredients": ["x"],
        "allergens": [],
        "may_contain": [],
    }
    return Card.model_validate(base | fields)


def turn(*cards: Card, status: str = "ok") -> Turn:
    return Turn.model_validate(
        {"user": "u", "say": "hi", "status": status, "seconds": 1.0, "cards": list(cards)}
    )


def expect(**fields: Any) -> Expect:
    return Expect.model_validate(fields)


def failed(rules: Expect, t: Turn) -> list[str]:
    return [c.name for c in grade_turn(rules, t, "turn 1") if not c.passed]


def test_forbidden_allergen_and_unwarned_trace_fail() -> None:
    nuts = expect(forbid_allergens=["peanut", "tree_nut"])
    assert failed(nuts, turn(card("Sorbet"))) == []
    assert failed(nuts, turn(card("Peanut bowl", allergens=["peanut"]))) == ["turn 1 allergens"]
    cake = card("Lava cake", may_contain=["tree_nut"])
    assert failed(nuts, turn(cake)) == ["turn 1 allergens"]
    warned = card("Lava cake", may_contain=["tree_nut"], may_contain_warnings=["tree_nut"])
    assert failed(nuts, turn(warned)) == []


def test_diet_cards_and_price_limits() -> None:
    wings = card("Wings", is_vegetarian=False, is_vegan=False, price_sar=Decimal("38.00"))
    cake = card("Cake", is_vegan=False)
    assert failed(expect(diet="vegetarian"), turn(cake)) == []
    assert failed(expect(diet="vegan"), turn(cake)) == ["turn 1 diet vegan"]
    assert failed(expect(diet="vegetarian"), turn(wings)) == ["turn 1 diet vegetarian"]
    assert failed(expect(max_price_sar=30), turn(wings)) == ["turn 1 max price 30"]
    assert failed(expect(cards="some"), turn()) == ["turn 1 cards some"]
    assert failed(expect(cards="none"), turn(cake)) == ["turn 1 cards none"]


def test_status_must_match_and_a_failed_turn_skips_card_checks() -> None:
    assert failed(expect(refused=True), turn(status="refused")) == []
    assert failed(expect(refused=True), turn()) == ["turn 1 status"]
    assert failed(expect(cards="some"), turn(status="timeout")) == ["turn 1 status"]


def test_prices_must_be_on_the_menu_or_said_by_the_user() -> None:
    assert stated_prices("Wagyu is 85 SAR, or SAR 16.00 for a drink") == [
        Decimal(85),
        Decimal("16.00"),
    ]
    menu = {"Double Wagyu Burger": Decimal("85.00"), "Fresh Lemon Mint": Decimal("16.00")}
    assert grade_prices("The Double Wagyu Burger is 85 SAR.", menu, [], "t").passed
    assert grade_prices("Under 30 SAR: try X.", menu, ["I have 30 SAR"], "t").passed
    invented = grade_prices("Sushi is 55 SAR.", menu, ["hi"], "t")
    assert (invented.passed, invented.detail) == (False, "55")


def test_a_price_must_match_the_dish_it_follows() -> None:
    menu = {"Double Wagyu Burger": Decimal("85.00"), "Fresh Lemon Mint": Decimal("16.00")}
    swapped = grade_prices("The Double Wagyu Burger is 16 SAR.", menu, [], "t")
    assert (swapped.passed, swapped.detail) == (False, "Double Wagyu Burger 16 (menu 85.00)")
    both = "Fresh Lemon Mint (16 SAR) or the double wagyu burger (SAR 85)."
    assert grade_prices(both, menu, [], "t").passed
    new_sentence = "Try the Fresh Lemon Mint. Most mains are 85 SAR."
    assert grade_prices(new_sentence, menu, [], "t").passed


def test_profile_expectations() -> None:
    stored = [
        StoredFact(kind="diet", value="vegetarian", status="active"),
        StoredFact(kind="diet", value="vegan", status="superseded"),
    ]
    good = ProfileExpect.model_validate(
        {"active": [["diet", "vegetarian"]], "superseded": [["diet", "vegan"]], "exact": True}
    )
    assert all(c.passed for c in grade_profile("u", good, stored))
    bad = ProfileExpect.model_validate({"not_active": [["diet", "vegetarian"]], "exact": True})
    results = {c.name: c.passed for c in grade_profile("u", bad, stored)}
    assert results == {"u not active": False, "u nothing else active": False}
    assert all(c.passed for c in grade_profile("u", ProfileExpect(exact=True), []))


def test_prices_are_kept_per_restaurant_and_unknown_ones_fail() -> None:
    restaurants = load_restaurants()
    prices = prices_by_restaurant(restaurants, ["corner-table"])
    assert prices["corner-table"]["Mango Sorbet"] == Decimal("22.00")
    assert "Mango Sorbet" not in prices["golden-dragon"]
    with pytest.raises(ValueError, match="nowhere"):
        prices_by_restaurant(restaurants, ["nowhere"])
