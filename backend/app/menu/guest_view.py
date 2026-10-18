"""Menu items as one guest sees them: every field, plus what conflicts with their profile.

One shape for the model's tool results, the chat cards and the menu page, so
each shows the same allergens, prices, options and warnings.
"""

from pydantic import Field

from app.menu.allergens import Allergen
from app.menu.constraints import HardConstraints
from app.menu.option_schemas import OptionGroupBase, OptionOut
from app.menu.schemas import MenuItemBase, MenuItemOut
from app.menu.taste import NO_TASTES, Tastes, liked, taste_notes, today_pick


class GuestOption(OptionOut):
    conflicts_with_guest: list[str]
    """Why this guest must not pick it (their saved allergies or diet); empty if they may."""
    may_contain_warnings: list[Allergen]
    """Trace allergens of this option that the guest avoids: confirm with staff."""


class GuestOptionGroup(OptionGroupBase):
    id: int
    options: list[GuestOption]


class GuestItem(MenuItemBase):
    id: int
    option_groups: list[GuestOptionGroup] = Field(default_factory=list[GuestOptionGroup])
    conflicts_with_guest: list[str] = Field(default_factory=list[str])
    """Why no way of ordering it suits the guest; empty if one does."""
    may_contain_warnings: list[Allergen] = Field(default_factory=list[Allergen])
    """Traces the guest avoids that every suitable way of ordering it carries."""
    taste_notes: list[str] = Field(default_factory=list[str])
    """Soft reasons it may not suit the guest today (dislikes, budget, ...); never a block."""
    liked: bool = False
    today_pick: bool = False
    """It has a food the guest wants on this weekday (a day like)."""


def guest_item(
    item: MenuItemOut, constraints: HardConstraints, tastes: Tastes = NO_TASTES
) -> GuestItem:
    conflicts = constraints.option_conflicts(item)
    groups = [
        GuestOptionGroup(
            **group.model_dump(exclude={"options"}),
            options=[
                GuestOption(
                    **o.model_dump(),
                    conflicts_with_guest=conflicts.get(o.id, []),
                    may_contain_warnings=constraints.may_contain_warnings(o),
                )
                for o in group.options
            ],
        )
        for group in item.option_groups
    ]
    return GuestItem(
        **item.model_dump(exclude={"option_groups"}),
        option_groups=groups,
        conflicts_with_guest=constraints.item_violations(item),
        may_contain_warnings=constraints.item_may_contain_warnings(item),
        taste_notes=taste_notes(item, tastes),
        liked=liked(item, tastes),
        today_pick=today_pick(item, tastes),
    )
