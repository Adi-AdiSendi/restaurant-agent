"""Resolve an item with chosen options and removals into what is priced, checked and shown.

Pure: no database. Leaving an ingredient out never removes an allergen
(ADR 0018); kitchens share surfaces, so a wrong "safe" is the failure that hurts.
"""

from collections.abc import Sequence
from decimal import Decimal

from pydantic import BaseModel

from app.menu.allergens import Allergen
from app.menu.option_schemas import OptionOut
from app.menu.schemas import MenuItemOut


class ConfigurationError(ValueError):
    """The choices do not make a valid order of this item. The message says why."""


class Configuration(BaseModel):
    item_id: int
    option_ids: list[int]
    removed: list[str]
    unit_price_sar: Decimal
    allergens: list[Allergen]
    may_contain: list[Allergen]
    is_vegetarian: bool
    is_vegan: bool
    spice_level: int
    kcal: int | None
    """Estimated kcal of one, with these options; None if the dish has no estimate."""


def _chosen(item: MenuItemOut, option_ids: Sequence[int]) -> list[OptionOut]:
    if len(set(option_ids)) != len(option_ids):
        raise ConfigurationError("An option is chosen more than once.")
    offered = {o.id: o for g in item.option_groups for o in g.options}
    unknown = [i for i in option_ids if i not in offered]
    if unknown:
        raise ConfigurationError(f"Options {unknown} are not offered with {item.name}.")
    chosen = set(option_ids)
    for group in item.option_groups:
        count = sum(1 for o in group.options if o.id in chosen)
        if count < group.min_choices:
            raise ConfigurationError(f"Choose at least {group.min_choices} {group.name}.")
        if count > group.max_choices:
            raise ConfigurationError(f"Choose at most {group.max_choices} {group.name}.")
    return [offered[i] for i in option_ids]


def configure(
    item: MenuItemOut, option_ids: Sequence[int], removed: Sequence[str]
) -> Configuration:
    options = _chosen(item, option_ids)
    not_removable = sorted(set(removed) - set(item.removable))
    if not_removable:
        raise ConfigurationError(f"{not_removable} cannot be left out of {item.name}.")
    allergens = set(item.allergens).union(*(o.allergens for o in options))
    may_contain = set(item.may_contain).union(*(o.may_contain for o in options)) - allergens
    return Configuration(
        item_id=item.id,
        option_ids=list(option_ids),
        removed=list(dict.fromkeys(removed)),
        unit_price_sar=item.price_sar + sum((o.price_delta_sar for o in options), Decimal(0)),
        allergens=sorted(allergens),
        may_contain=sorted(may_contain),
        is_vegetarian=item.is_vegetarian and all(o.is_vegetarian for o in options),
        is_vegan=item.is_vegan and all(o.is_vegan for o in options),
        spice_level=max([item.spice_level, *(o.spice_level for o in options)]),
        kcal=None if item.kcal is None else max(item.kcal + sum(o.kcal_delta for o in options), 0),
    )
