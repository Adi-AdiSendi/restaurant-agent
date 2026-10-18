"""What the cart tools return. Every result carries the whole cart, priced by the server."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.orders.schemas import CartLineOut, CartOut, NewLine, OrderOut
from app.tools.errors import ToolError, invalid_arguments

NO_PARAMETERS: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": [],
    "properties": {},
}


class NoArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")


def check_no_arguments(arguments: str) -> ToolError | None:
    try:
        NoArguments.model_validate_json(arguments or "{}")
    except ValidationError as exc:
        return invalid_arguments(exc)
    return None


class CartView(BaseModel):
    cart: CartOut


class CartChange(BaseModel):
    """One change the guest asked for, as the server made it."""

    action: Literal["added", "updated", "removed", "cleared"]
    quantity: int
    """How many were added, the new quantity, or how many were removed (all, if cleared)."""
    line: CartLineOut | None
    """The line as it is now (as it was, for a removal)."""
    left_out_for_dislikes: list[str] = Field(default_factory=list[str])
    """Removable ingredients left out because the guest dislikes them. Tell the guest."""
    cart: CartOut


class CheckoutProposal(BaseModel):
    cart: CartOut
    note: str


class RecentOrders(BaseModel):
    orders: list[OrderOut]


def line_for(cart: CartOut, new: NewLine) -> CartLineOut | None:
    """The cart line holding this choice (identical choices share one line)."""
    for line in cart.lines:
        if (
            line.item_id == new.item_id
            and sorted(o.id for o in line.options) == sorted(new.option_ids)
            and set(line.removed) == set(new.removed)
        ):
            return line
    return None
