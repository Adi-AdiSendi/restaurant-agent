"""Brief section 3 menu requirements (M1 to M5), checked on every restaurant file."""

import pytest

from app.menu.restaurant_schemas import RestaurantFile
from scripts.seed_menu import load_restaurants

RESTAURANTS = load_restaurants()
CORNER_TABLE = RESTAURANTS[0]
by_slug = pytest.mark.parametrize("restaurant", RESTAURANTS, ids=lambda r: r.slug)


def test_corner_table_comes_first() -> None:
    assert CORNER_TABLE.slug == "corner-table"


@by_slug
def test_m1_at_least_12_items_across_3_categories(restaurant: RestaurantFile) -> None:
    assert len(restaurant.items) >= 12
    assert len({item.category for item in restaurant.items}) >= 3


@by_slug
def test_m3_vegetarian_choices(restaurant: RestaurantFile) -> None:
    assert any(item.is_vegetarian for item in restaurant.items)


@by_slug
def test_m5_every_item_lists_ingredients(restaurant: RestaurantFile) -> None:
    assert all(item.ingredients for item in restaurant.items)


@by_slug
def test_every_category_is_used(restaurant: RestaurantFile) -> None:
    assert {item.category for item in restaurant.items} == set(restaurant.categories)


def test_restaurant_names_and_slugs_are_unique() -> None:
    assert (
        len({r.name for r in RESTAURANTS}) == len({r.slug for r in RESTAURANTS}) == len(RESTAURANTS)
    )


# Corner Table is the v1 menu; its tests and evals depend on these exact facts.
def test_corner_table_prices_differ() -> None:
    assert len({item.price_sar for item in CORNER_TABLE.items}) == len(CORNER_TABLE.items)


def test_corner_table_has_meat_vegetarian_and_vegan() -> None:
    assert any(not item.is_vegetarian for item in CORNER_TABLE.items)
    assert any(item.is_vegan for item in CORNER_TABLE.items)


def test_corner_table_uses_every_spice_level() -> None:
    assert {item.spice_level for item in CORNER_TABLE.items} == {0, 1, 2, 3}


def test_corner_table_allergen_free_items_are_explicit() -> None:
    allergen_free = [item.name for item in CORNER_TABLE.items if not item.allergens]
    assert allergen_free == ["Mango Sorbet", "Fresh Lemon Mint"]
