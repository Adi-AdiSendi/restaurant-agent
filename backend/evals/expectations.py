"""What must be true after a turn, and of each user's profile at the end of a case."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.memory.vocabulary import Diet, Kind
from app.menu.allergens import Allergen


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class LineExpect(Strict):
    """One cart line. `options` and `removed`, when given, must match exactly (any order)."""

    name: str
    quantity: int = 1
    options: list[str] | None = None
    removed: list[str] | None = None


class Expect(Strict):
    cards: Literal["any", "some", "none"] = "any"
    forbid_allergens: list[Allergen] = Field(default_factory=list[Allergen])
    diet: Diet | None = None
    max_price_sar: Decimal | None = None
    prices: bool = False
    """Every "NN SAR" in the reply must be a menu price or a number the user said."""
    refused: bool = False
    """The turn must be refused (posting into another user's conversation)."""
    judge: str | None = None
    """A pass criterion for the reply text, graded by the LLM judge."""
    cart: list[LineExpect] | None = None
    """The speaker's cart after the turn, exactly these lines; [] means empty."""
    orders: int | None = None
    """How many orders the speaker has after the turn."""
    checkout_card: bool | None = None
    """Whether the reply shows a checkout card."""
    menu: str | None = None
    """The reply shows a menu block of exactly this category."""


Fact = tuple[Kind, str]


class ProfileExpect(Strict):
    active: list[Fact] = Field(default_factory=list[Fact])
    superseded: list[Fact] = Field(default_factory=list[Fact])
    not_active: list[Fact] = Field(default_factory=list[Fact])
    exact: bool = False
    """The active facts must be exactly `active`, nothing more."""
