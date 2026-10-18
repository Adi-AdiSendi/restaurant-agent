"""What the cart and order functions take and return. Prices are always computed here."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.menu.allergens import Allergen

MAX_QUANTITY = 20
Fulfilment = Literal["pickup", "dine_in"]
OrderStatus = Literal["placed", "preparing", "ready"]


class NewLine(BaseModel):
    """One dish as the guest configured it. There is no price field: the server prices it."""

    model_config = ConfigDict(extra="forbid")

    item_id: int = Field(ge=1)
    quantity: int = Field(default=1, ge=1, le=MAX_QUANTITY)
    option_ids: list[int] = Field(default_factory=list[int], max_length=20)
    removed: list[str] = Field(default_factory=list[str], max_length=20)


class LineOption(BaseModel):
    id: int
    name: str
    price_delta_sar: Decimal


class CartLineOut(BaseModel):
    id: int
    item_id: int
    name: str
    quantity: int
    options: list[LineOption]
    removed: list[str]
    unit_price_sar: Decimal | None
    line_total_sar: Decimal | None
    kcal: int | None = None
    """Estimated kcal of one, with its options; None if the dish has no estimate."""
    allergens: list[Allergen]
    conflicts_with_guest: list[str]
    may_contain_warnings: list[Allergen]
    problem: str | None
    """Why this line cannot be ordered any more (the menu changed); None if it can."""


class CartRestaurant(BaseModel):
    slug: str
    name: str


class CartOut(BaseModel):
    restaurant: CartRestaurant | None
    lines: list[CartLineOut]
    total_sar: Decimal
    item_count: int
    kcal: int = 0
    """Estimated kcal of the whole cart, from the lines that have an estimate."""


class OrderLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_name: str
    quantity: int
    unit_price_sar: Decimal
    option_names: list[str]
    removed: list[str]
    allergens: list[Allergen]
    kcal: int | None = None
    photo: str | None = None
    """The dish's photo today (`<restaurant>/<name>`); None if it has none or is gone."""


class OrderSummary(BaseModel):
    id: int
    restaurant: CartRestaurant
    fulfilment: Fulfilment
    total_sar: Decimal
    item_count: int
    placed_at: datetime
    status: OrderStatus
    photos: list[str] = Field(default_factory=list[str])
    """Photos of the dishes in the order, in order, at most 4, for the history list."""
    kcal: int | None = None
    """Estimated kcal of the whole order; None if no line had an estimate."""


class OrderOut(OrderSummary):
    lines: list[OrderLineOut]
