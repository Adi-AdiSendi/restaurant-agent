"""What one chat turn returns."""

from pydantic import BaseModel, Field

from app.menu.allergens import Allergen
from app.menu.constraints import HardConstraints
from app.menu.schemas import MenuItemOut
from app.tools.menu_views import ToolItem, tool_item


class Card(ToolItem):
    """A recommended item as the UI shows it: every option with its conflicts for this
    guest, and any trace-allergen warning."""

    may_contain_warnings: list[Allergen] = Field(default_factory=list[Allergen])


class AgentReply(BaseModel):
    reply: str
    items: list[Card]


def cards_for(items: list[MenuItemOut], constraints: HardConstraints) -> list[Card]:
    return [
        Card(
            **tool_item(item, constraints).model_dump(),
            may_contain_warnings=constraints.may_contain_warnings(item),
        )
        for item in items
    ]
