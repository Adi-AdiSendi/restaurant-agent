"""A guest's hard constraints (allergies and diet), applied to every menu search."""

from pydantic import BaseModel, ConfigDict, Field

from app.menu.allergens import Allergen
from app.menu.schemas import MenuFilter, MenuItemOut


class HardConstraints(BaseModel):
    """Built from the stored profile by the server, never from model arguments."""

    model_config = ConfigDict(frozen=True)

    excluded_allergens: frozenset[Allergen] = Field(default_factory=frozenset[Allergen])
    vegetarian: bool = False
    vegan: bool = False

    def violations(self, item: MenuItemOut) -> list[str]:
        """Why this item must not be recommended to this guest; empty if it may."""
        reasons = sorted(a.value for a in set(item.allergens) & self.excluded_allergens)
        if self.vegan and not item.is_vegan:
            reasons.append("not vegan")
        elif self.vegetarian and not item.is_vegetarian:
            reasons.append("not vegetarian")
        return reasons

    def may_contain_warnings(self, item: MenuItemOut) -> list[Allergen]:
        """Trace allergens the guest avoids: allowed, but they should confirm with staff."""
        return sorted(set(item.may_contain) & self.excluded_allergens)

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
