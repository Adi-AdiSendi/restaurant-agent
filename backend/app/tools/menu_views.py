"""Menu items as the model sees them: every field, plus each option's conflicts.

The model gets complete records (allergens, prices, diet flags of every
option), so it never has to guess which choice suits the guest.
"""

from pydantic import Field

from app.menu.allergens import Allergen
from app.menu.constraints import HardConstraints
from app.menu.option_schemas import OptionGroupBase, OptionOut
from app.menu.schemas import MenuItemBase, MenuItemOut


class ToolOption(OptionOut):
    conflicts_with_guest: list[str]
    """Why this guest must not pick it (their saved allergies or diet); empty if they may."""
    may_contain_warnings: list[Allergen]
    """Trace allergens of this option that the guest avoids: confirm with staff."""


class ToolOptionGroup(OptionGroupBase):
    id: int
    options: list[ToolOption]


class ToolItem(MenuItemBase):
    id: int
    option_groups: list[ToolOptionGroup] = Field(default_factory=list[ToolOptionGroup])


def tool_item(item: MenuItemOut, constraints: HardConstraints) -> ToolItem:
    conflicts = constraints.option_conflicts(item)
    groups = [
        ToolOptionGroup(
            **group.model_dump(exclude={"options"}),
            options=[
                ToolOption(
                    **o.model_dump(),
                    conflicts_with_guest=conflicts.get(o.id, []),
                    may_contain_warnings=constraints.may_contain_warnings(o),
                )
                for o in group.options
            ],
        )
        for group in item.option_groups
    ]
    return ToolItem(**item.model_dump(exclude={"option_groups"}), option_groups=groups)
