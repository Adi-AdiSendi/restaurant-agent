"""Pydantic shapes for menu data entering (seed) and leaving this module."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.menu.allergens import Allergen
from app.menu.categories import Category


class MenuItemFields(BaseModel):
    """One menu item without its database ID. Bounds mirror the table's CHECKs."""

    name: str = Field(min_length=1, max_length=80)
    category: Category
    description: str = Field(min_length=1)
    price_sar: Decimal = Field(gt=0, max_digits=8, decimal_places=2)
    is_vegetarian: bool
    is_vegan: bool
    spice_level: int = Field(ge=0, le=3)
    ingredients: list[str] = Field(min_length=1)
    allergens: list[Allergen]
    may_contain: list[Allergen]


class MenuItemOut(MenuItemFields):
    model_config = ConfigDict(from_attributes=True)

    id: int


class MenuFilter(BaseModel):
    """Every field is optional; an empty filter returns the whole menu."""

    category: Category | None = None
    max_price_sar: Decimal | None = Field(default=None, gt=0)
    max_spice: int | None = Field(default=None, ge=0, le=3)
    vegetarian: bool = False
    vegan: bool = False
    exclude_allergens: list[Allergen] = Field(default_factory=list[Allergen])
    text: str | None = Field(default=None, max_length=100)
