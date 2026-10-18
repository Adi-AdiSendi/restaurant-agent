"""Option groups and options, as seeded and as read. Bounds mirror the tables' CHECKs."""

from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.menu.allergens import Allergen


class OptionFields(BaseModel):
    """One choice. Picking it adds its allergens and can make a dish non-vegetarian."""

    name: str = Field(min_length=1, max_length=60)
    price_delta_sar: Decimal = Field(ge=0, max_digits=8, decimal_places=2)
    allergens: list[Allergen]
    may_contain: list[Allergen]
    is_vegetarian: bool
    is_vegan: bool
    spice_level: int = Field(ge=0, le=3)
    kcal_delta: int = Field(default=0, ge=-1000, le=2000)
    """Estimated kcal this choice adds (or saves) against the dish's base."""

    @model_validator(mode="after")
    def _vegan_is_vegetarian(self) -> Self:
        if self.is_vegan and not self.is_vegetarian:
            raise ValueError(f"option {self.name!r} is vegan but not vegetarian")
        return self


class OptionOut(OptionFields):
    model_config = ConfigDict(from_attributes=True)

    id: int


class OptionGroupBase(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    min_choices: int = Field(ge=0)
    max_choices: int = Field(ge=1)

    @property
    def required(self) -> bool:
        return self.min_choices > 0


def _check_group(group: OptionGroupBase, option_names: list[str]) -> None:
    if group.min_choices > group.max_choices:
        raise ValueError(f"group {group.name!r}: min_choices is above max_choices")
    if group.min_choices > len(option_names):
        raise ValueError(f"group {group.name!r}: fewer options than min_choices")
    if len(set(option_names)) != len(option_names):
        raise ValueError(f"group {group.name!r}: option names repeat")


class OptionGroupFields(OptionGroupBase):
    options: list[OptionFields] = Field(min_length=1)

    @model_validator(mode="after")
    def _valid(self) -> Self:
        _check_group(self, [o.name for o in self.options])
        return self


class OptionGroupOut(OptionGroupBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    options: list[OptionOut]
