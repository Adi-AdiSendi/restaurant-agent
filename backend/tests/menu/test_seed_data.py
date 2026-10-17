"""Brief section 3 menu requirements (M1 to M5), checked on the seed file."""

from scripts.seed_menu import load_menu

MENU = load_menu()


def test_m1_at_least_12_items_across_3_categories() -> None:
    assert len(MENU) >= 12
    assert len({item.category for item in MENU}) >= 3


def test_names_are_unique() -> None:
    assert len({item.name for item in MENU}) == len(MENU)


def test_m2_prices_differ() -> None:
    assert len({item.price_sar for item in MENU}) == len(MENU)


def test_m3_vegetarian_and_non_vegetarian() -> None:
    assert any(item.is_vegetarian for item in MENU)
    assert any(not item.is_vegetarian for item in MENU)
    assert any(item.is_vegan for item in MENU)


def test_vegan_items_are_vegetarian() -> None:
    assert all(item.is_vegetarian for item in MENU if item.is_vegan)


def test_m4_every_spice_level_is_used() -> None:
    assert {item.spice_level for item in MENU} == {0, 1, 2, 3}


def test_m5_every_item_lists_ingredients() -> None:
    assert all(item.ingredients for item in MENU)


def test_m5_allergen_free_items_are_explicit() -> None:
    allergen_free = [item.name for item in MENU if not item.allergens]
    assert allergen_free == ["Mango Sorbet", "Fresh Lemon Mint"]
