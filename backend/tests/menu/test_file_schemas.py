"""Restaurant files are validated before anything reaches the database."""

from typing import Any

import pytest
from pydantic import ValidationError

from app.menu.restaurant_schemas import RestaurantFile


def option(name: str, **extra: Any) -> dict[str, Any]:
    base: dict[str, Any] = {"name": name, "price_delta_sar": "0.00", "allergens": []}
    flags: dict[str, Any] = {"may_contain": [], "is_vegetarian": True, "is_vegan": True}
    return base | flags | {"spice_level": 0} | extra


def item(name: str = "Latte", **extra: Any) -> dict[str, Any]:
    milk = {"name": "Milk", "min_choices": 1, "max_choices": 1, "options": [option("Oat")]}
    base: dict[str, Any] = {"name": name, "category": "drinks", "description": "Test."}
    flags: dict[str, Any] = {"price_sar": "14.00", "is_vegetarian": True, "is_vegan": True}
    rest: dict[str, Any] = {"spice_level": 0, "ingredients": ["espresso", "sugar"]}
    lists: dict[str, Any] = {"allergens": [], "may_contain": [], "option_groups": [milk]}
    return base | flags | rest | lists | extra


def restaurant(*items: dict[str, Any], **extra: Any) -> dict[str, Any]:
    base: dict[str, Any] = {"slug": "test-cafe", "name": "Test Cafe", "cuisine": "Cafe"}
    rest: dict[str, Any] = {"tagline": "Test.", "accent_color": "#123456", "categories": ["drinks"]}
    return base | rest | {"items": list(items) or [item()]} | extra


def test_valid_file_is_accepted() -> None:
    parsed = RestaurantFile.model_validate(restaurant(item(removable=["sugar"])))
    assert parsed.items[0].option_groups[0].required


@pytest.mark.parametrize(
    "bad",
    [
        restaurant(item(category="mains")),
        restaurant(item(), item()),
        restaurant(item(removable=["salt"])),
        restaurant(item(is_vegan=True, is_vegetarian=False)),
        restaurant(
            item(
                option_groups=[
                    {"name": "Milk", "min_choices": 2, "max_choices": 2, "options": [option("Oat")]}
                ]
            )
        ),
        restaurant(
            item(
                option_groups=[
                    {
                        "name": "Milk",
                        "min_choices": 2,
                        "max_choices": 1,
                        "options": [option("Oat"), option("Soy")],
                    }
                ]
            )
        ),
        restaurant(
            item(
                option_groups=[
                    {
                        "name": "Milk",
                        "min_choices": 0,
                        "max_choices": 2,
                        "options": [option("Oat"), option("Oat")],
                    }
                ]
            )
        ),
        restaurant(
            item(
                option_groups=[
                    {
                        "name": "Milk",
                        "min_choices": 0,
                        "max_choices": 1,
                        "options": [option("Oat", is_vegetarian=False)],
                    }
                ]
            )
        ),
        restaurant(categories=["drinks", "drinks"]),
        restaurant(slug="Test Cafe"),
        restaurant(accent_color="#ABCDEF"),
    ],
    ids=[
        "unlisted category",
        "repeated item",
        "removable not an ingredient",
        "vegan not veg",
        "min above options",
        "min above max",
        "repeated option",
        "vegan option not veg",
        "repeated category",
        "bad slug",
        "upper-case colour",
    ],
)
def test_invalid_file_is_rejected(bad: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        RestaurantFile.model_validate(bad)
