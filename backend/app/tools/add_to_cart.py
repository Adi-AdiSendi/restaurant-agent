"""add_to_cart: add one configured dish of this restaurant to the guest's cart."""

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.menu.queries import get_item
from app.menu.schemas import MenuItemOut
from app.orders.cart_add import add_line
from app.orders.schemas import MAX_QUANTITY, CartLineOut, CartOut, NewLine
from app.tools.cart_results import CartChange
from app.tools.cart_write import cart_write
from app.tools.context import ToolContext
from app.tools.dislikes import disliked_removables
from app.tools.errors import ToolError, invalid_arguments

NAME = "add_to_cart"

DESCRIPTION = """Add a dish of this restaurant to the guest's cart, only when the guest \
asks for it. The server checks the choice and sets the price.
Inputs (all required):
- item_id: from search_menu or get_item.
- quantity: 1 to 20.
- option_ids: one option id per choice the guest made; every group with min_choices \
of 1 or more needs its choices. Ask the guest when a required choice is not clear.
- removed: removable ingredients the guest asked to leave out.
- keep_ingredients: ingredients the guest wants this time although they dislike them; \
usually [].
Example: {"item_id": 41, "quantity": 1, "option_ids": [12, 15], "removed": [], \
"keep_ingredients": []}
A removable ingredient the guest dislikes is left out and listed in left_out_for_dislikes: \
tell the guest. This does not make disliked dishes fine to recommend.
A choice that breaks their allergies or diet is refused (error_category "conflict"): \
explain why and never offer to add it anyway.
Do NOT use it to place an order, or for dishes of another restaurant."""

PARAMETERS: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["item_id", "quantity", "option_ids", "removed", "keep_ingredients"],
    "properties": {
        "item_id": {"type": "integer"},
        "quantity": {"type": "integer"},
        "option_ids": {"type": "array", "items": {"type": "integer"}},
        "removed": {"type": "array", "items": {"type": "string"}},
        "keep_ingredients": {"type": "array", "items": {"type": "string"}},
    },
}


class AddToCartArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: int = Field(ge=1)
    quantity: int = Field(ge=1, le=MAX_QUANTITY)
    option_ids: list[int] = Field(max_length=20)
    removed: list[str] = Field(max_length=20)
    keep_ingredients: list[str] = Field(max_length=20)


def _line(cart: CartOut, new: NewLine) -> CartLineOut | None:
    """The cart line holding this choice (identical choices share one line)."""
    for line in cart.lines:
        if (
            line.item_id == new.item_id
            and sorted(o.id for o in line.options) == sorted(new.option_ids)
            and set(line.removed) == set(new.removed)
        ):
            return line
    return None


async def handle(arguments: str, context: ToolContext) -> CartChange | ToolError:
    try:
        args = AddToCartArgs.model_validate_json(arguments)
    except ValidationError as exc:
        return invalid_arguments(exc)
    row = await get_item(context.session, context.restaurant_id, args.item_id)
    if row is None:
        message = f"This restaurant has no menu item with id {args.item_id}."
        return ToolError(error_category="not_found", retryable=False, message=message)
    item = MenuItemOut.model_validate(row)
    disliked = disliked_removables(item.removable, context.dislikes, args.keep_ingredients)
    left_out = [r for r in disliked if r not in args.removed]
    new = NewLine(
        item_id=args.item_id,
        quantity=args.quantity,
        option_ids=args.option_ids,
        removed=[*args.removed, *left_out],
    )
    cart = await cart_write(
        context,
        lambda: add_line(
            context.session, context.user_id, context.restaurant_slug, new, context.constraints
        ),
    )
    if isinstance(cart, ToolError):
        return cart
    line = _line(cart, new)
    return CartChange(
        action="added", quantity=args.quantity, line=line, left_out_for_dislikes=left_out, cart=cart
    )
