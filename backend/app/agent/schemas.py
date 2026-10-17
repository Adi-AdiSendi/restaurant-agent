"""What one chat turn returns."""

from pydantic import BaseModel, Field

from app.menu.allergens import Allergen
from app.menu.schemas import MenuItemOut


class Card(MenuItemOut):
    """A recommended item as the UI shows it, with any trace-allergen warning."""

    may_contain_warnings: list[Allergen] = Field(default_factory=list[Allergen])


class AgentReply(BaseModel):
    reply: str
    items: list[Card]
