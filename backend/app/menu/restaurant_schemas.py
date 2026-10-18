"""Restaurants as written in `data/restaurants/*.json` and as the API returns them."""

from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.menu.restaurant import ACCENT_PATTERN, CATEGORY_PATTERN, PHOTO_PATTERN, SLUG_PATTERN
from app.menu.schemas import MenuItemFields

CategorySlug = Annotated[str, Field(pattern=CATEGORY_PATTERN, max_length=40)]


class RestaurantFields(BaseModel):
    slug: str = Field(pattern=SLUG_PATTERN, max_length=40)
    name: str = Field(min_length=1, max_length=60)
    cuisine: str = Field(min_length=1, max_length=40)
    tagline: str = Field(min_length=1)
    accent_color: str = Field(pattern=ACCENT_PATTERN)
    categories: list[CategorySlug] = Field(min_length=1)
    """In the order the menu shows them."""
    photo: str | None = Field(default=None, pattern=PHOTO_PATTERN, max_length=100)
    """The cover photo; None shows the accent colour only."""

    @model_validator(mode="after")
    def _unique_categories(self) -> Self:
        if len(set(self.categories)) != len(self.categories):
            raise ValueError(f"{self.slug}: categories repeat")
        return self


class RestaurantOut(RestaurantFields):
    model_config = ConfigDict(from_attributes=True)

    id: int


class RestaurantFile(RestaurantFields):
    """One restaurant file: the source of truth for its menu."""

    items: list[MenuItemFields] = Field(min_length=1)

    @model_validator(mode="after")
    def _items(self) -> Self:
        names = [i.name for i in self.items]
        if len(set(names)) != len(names):
            raise ValueError(f"{self.slug}: item names repeat")
        stray = sorted({i.category for i in self.items} - set(self.categories))
        if stray:
            raise ValueError(f"{self.slug}: items use unlisted categories {stray}")
        return self
