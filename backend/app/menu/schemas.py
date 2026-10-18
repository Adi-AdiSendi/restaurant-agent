"""Pydantic shapes for menu data entering (seed) and leaving this module."""

from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.menu.allergens import Allergen
from app.menu.option_schemas import OptionGroupFields, OptionGroupOut
from app.menu.restaurant import CATEGORY_PATTERN, PHOTO_PATTERN


class MenuItemBase(BaseModel):
    """One menu item's own fields: its base, without options. Bounds mirror the CHECKs."""

    name: str = Field(min_length=1, max_length=80)
    category: str = Field(pattern=CATEGORY_PATTERN, max_length=40)
    description: str = Field(min_length=1)
    price_sar: Decimal = Field(gt=0, max_digits=8, decimal_places=2)
    is_vegetarian: bool
    is_vegan: bool
    spice_level: int = Field(ge=0, le=3)
    ingredients: list[str] = Field(min_length=1)
    allergens: list[Allergen]
    may_contain: list[Allergen]
    removable: list[str] = Field(default_factory=list[str])
    """Ingredients a guest may leave out. Leaving one out never removes an allergen."""
    photo: str | None = Field(default=None, pattern=PHOTO_PATTERN, max_length=100)
    kcal: int | None = Field(default=None, ge=1, le=3000)
    """Estimated kcal of the base dish (typical portion); None if not estimated."""
    """A similar dish's photo, credited in docs/photo-credits.md; None shows an icon."""

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.is_vegan and not self.is_vegetarian:
            raise ValueError(f"{self.name!r} is vegan but not vegetarian")
        unknown = set(self.removable) - set(self.ingredients)
        if unknown:
            raise ValueError(f"{self.name!r}: removable {sorted(unknown)} not in ingredients")
        return self


class MenuItemFields(MenuItemBase):
    """One item as written in a restaurant file (seed input)."""

    option_groups: list[OptionGroupFields] = Field(default_factory=list[OptionGroupFields])

    @model_validator(mode="after")
    def _unique_groups(self) -> Self:
        names = [g.name for g in self.option_groups]
        if len(set(names)) != len(names):
            raise ValueError(f"{self.name!r}: option group names repeat")
        return self


class MenuItemOut(MenuItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    option_groups: list[OptionGroupOut] = Field(default_factory=list[OptionGroupOut])


class MenuFilter(BaseModel):
    """Every field is optional; an empty filter returns the whole menu."""

    category: str | None = Field(default=None, max_length=40)
    max_price_sar: Decimal | None = Field(default=None, gt=0)
    max_spice: int | None = Field(default=None, ge=0, le=3)
    vegetarian: bool = False
    vegan: bool = False
    exclude_allergens: list[Allergen] = Field(default_factory=list[Allergen])
    text: str | None = Field(default=None, max_length=100)
