"""A guest's hard constraints (allergies and diet), applied to every menu search.

One rule (`violations`) checks anything with allergens and diet flags: an
item's base, one option, or a resolved configuration (`configure.py`).
"""

from collections.abc import Sequence
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.menu.allergens import Allergen
from app.menu.schemas import MenuFilter, MenuItemOut


class Checkable(Protocol):
    @property
    def allergens(self) -> Sequence[Allergen]: ...
    @property
    def may_contain(self) -> Sequence[Allergen]: ...
    @property
    def is_vegetarian(self) -> bool: ...
    @property
    def is_vegan(self) -> bool: ...


class HardConstraints(BaseModel):
    """Built from the stored profile by the server, never from model arguments."""

    model_config = ConfigDict(frozen=True)

    excluded_allergens: frozenset[Allergen] = Field(default_factory=frozenset[Allergen])
    vegetarian: bool = False
    vegan: bool = False

    def violations(self, food: Checkable) -> list[str]:
        """Why this must not be served to this guest; empty if it may."""
        reasons = sorted(a.value for a in set(food.allergens) & self.excluded_allergens)
        if self.vegan and not food.is_vegan:
            reasons.append("not vegan")
        elif self.vegetarian and not food.is_vegetarian:
            reasons.append("not vegetarian")
        return reasons

    def item_violations(self, item: MenuItemOut) -> list[str]:
        """Why no way of ordering this item suits the guest; empty if one does.

        The base must fit, and every required group must keep enough fitting options.
        """
        reasons = self.violations(item)
        for group in item.option_groups:
            fitting = [o for o in group.options if not self.violations(o)]
            if len(fitting) < group.min_choices:
                reasons.append(f"no {group.name.lower()} choice fits")
        return reasons

    def option_conflicts(self, item: MenuItemOut) -> dict[int, list[str]]:
        """Option ID -> why the guest must not pick it; options that fit are left out."""
        return {
            option.id: reasons
            for group in item.option_groups
            for option in group.options
            if (reasons := self.violations(option))
        }

    def may_contain_warnings(self, food: Checkable) -> list[Allergen]:
        """Trace allergens the guest avoids: allowed, but they should confirm with staff."""
        return sorted(set(food.may_contain) & self.excluded_allergens)

    def restrict(self, menu_filter: MenuFilter) -> MenuFilter:
        """Merge into the model's filter. Only ever narrows the search, never widens it."""
        allergens = set(menu_filter.exclude_allergens) | self.excluded_allergens
        return menu_filter.model_copy(
            update={
                "exclude_allergens": sorted(allergens),
                "vegetarian": menu_filter.vegetarian or self.vegetarian or self.vegan,
                "vegan": menu_filter.vegan or self.vegan,
            }
        )


NO_CONSTRAINTS = HardConstraints()
