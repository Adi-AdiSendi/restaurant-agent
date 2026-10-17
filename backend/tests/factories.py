"""Menu items with options, built in memory for rule tests (no database)."""

from decimal import Decimal
from typing import Any

from app.menu.allergens import Allergen
from app.menu.constraints import HardConstraints
from app.menu.restaurant_schemas import RestaurantFile
from app.menu.schemas import MenuItemOut


def opt(option_id: int, name: str, **override: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {"id": option_id, "name": name, "price_delta_sar": "0.00"}
    flags: dict[str, Any] = {"allergens": [], "may_contain": [], "spice_level": 0}
    return fields | flags | {"is_vegetarian": True, "is_vegan": True} | override


def group(
    group_id: int, name: str, low: int, high: int, *options: dict[str, Any]
) -> dict[str, Any]:
    return {
        "id": group_id,
        "name": name,
        "min_choices": low,
        "max_choices": high,
        "options": list(options),
    }


def dish(**override: Any) -> MenuItemOut:
    fields: dict[str, Any] = {
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


def latte(*, with_oat: bool = True) -> MenuItemOut:
    """A required milk choice (oat fits a dairy and nut allergy) and optional syrups."""
    milks = [
        opt(101, "Whole milk", allergens=["dairy"], is_vegan=False),
        opt(102, "Oat milk", price_delta_sar="3.00", may_contain=["gluten"]),
        opt(103, "Almond milk", price_delta_sar="3.00", allergens=["tree_nut"]),
    ]
    syrup = group(
        11,
        "Syrup",
        0,
        2,
        opt(111, "Vanilla", price_delta_sar="2.00"),
        opt(112, "Honey", price_delta_sar="2.00", is_vegan=False),
        opt(113, "Chili", spice_level=2),
    )
    milk = group(10, "Milk", 1, 1, *(m for m in milks if with_oat or m["id"] != 102))
    return dish(
        name="Latte",
        price_sar=Decimal("14.00"),
        ingredients=["espresso", "sugar"],
        removable=["sugar"],
        option_groups=[milk, syrup],
    )


def guest(*allergens: Allergen, vegetarian: bool = False, vegan: bool = False) -> HardConstraints:
    return HardConstraints(
        excluded_allergens=frozenset(allergens), vegetarian=vegetarian, vegan=vegan
    )


def milk(name: str, *allergens: str) -> dict[str, Any]:
    flags: dict[str, Any] = {"may_contain": [], "is_vegetarian": True, "is_vegan": True}
    return {
        "name": name,
        "price_delta_sar": "0.00",
        "allergens": list(allergens),
        "spice_level": 0,
    } | flags


# A one-item restaurant whose latte needs a milk: whole (dairy) or oat (gluten).
TEST_CAFE = RestaurantFile.model_validate(
    {
        "slug": "test-cafe",
        "name": "Test Cafe",
        "cuisine": "Cafe",
        "tagline": "Test.",
        "accent_color": "#123456",
        "categories": ["coffee"],
        "items": [
            {
                "name": "Latte",
                "category": "coffee",
                "description": "Espresso and milk.",
                "price_sar": "14.00",
                "is_vegetarian": True,
                "is_vegan": True,
                "spice_level": 0,
                "ingredients": ["espresso"],
                "allergens": [],
                "may_contain": [],
                "option_groups": [
                    {
                        "name": "Milk",
                        "min_choices": 1,
                        "max_choices": 1,
                        "options": [milk("Whole milk", "dairy"), milk("Oat milk", "gluten")],
                    }
                ],
            }
        ],
    }
)
