"""What one chat turn returns."""

from pydantic import BaseModel

from app.menu.constraints import HardConstraints
from app.menu.guest_view import GuestItem, guest_item
from app.menu.schemas import MenuItemOut


class Card(GuestItem):
    """A recommended item as the UI shows it: every option with its conflicts for this
    guest, and any trace-allergen warning."""


class AgentReply(BaseModel):
    reply: str
    items: list[Card]


def cards_for(items: list[MenuItemOut], constraints: HardConstraints) -> list[Card]:
    return [Card(**guest_item(item, constraints).model_dump()) for item in items]
