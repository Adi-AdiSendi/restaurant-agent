"""add_to_cart: add one configured dish of this restaurant to the guest's cart."""

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.menu.queries import get_item
from app.menu.schemas import MenuItemOut
from app.orders.cart_add import add_line
from app.orders.schemas import MAX_QUANTITY, NewLine
from app.tools.cart_results import CartChange, line_for
from app.tools.cart_write import cart_write
from app.tools.context import ToolContext
from app.tools.dislikes import disliked_removables
from app.tools.errors import ToolError, invalid_arguments
from app.tools.packs import packs_for

NAME = "add_to_cart"

DESCRIPTION = """Add a dish of this restaurant to the guest's cart, only when the guest \
asks for it. The server checks the choice and sets the price.
Inputs (all required):
- item_id: from search_menu or get_item.
- quantity: 1 to 20 (for a dish sold in packs, the number of packs).
- units: for a dish sold in packs (pack_size above 1), the pieces the guest asked \
for, e.g. 5 dates; otherwise null. A count that is not whole packs is refused with \
the nearest counts: ask the guest before adding.
- option_ids: one option id per choice the guest made; every group with min_choices \
of 1 or more needs its choices. Ask the guest when a required choice is not clear.
- removed: removable ingredients the guest asked to leave out.
- keep_ingredients: ingredients the guest wants this time although they dislike them; \
usually [].
Example: {"item_id": 41, "quantity": 1, "units": null, "option_ids": [12, 15], \
"removed": [], "keep_ingredients": []}
A removable ingredient the guest dislikes is left out and listed in left_out_for_dislikes: \
tell the guest. This does not make disliked dishes fine to recommend.
A choice that breaks their allergies or diet is refused (error_category "conflict"): \
explain why and never offer to add it anyway.
Do NOT use it to place an order, or for dishes of another restaurant."""

PARAMETERS: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["item_id", "quantity", "units", "option_ids", "removed", "keep_ingredients"],
    "properties": {
        "item_id": {"type": "integer"},
        "quantity": {"type": "integer"},
        "units": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
        "option_ids": {"type": "array", "items": {"type": "integer"}},
        "removed": {"type": "array", "items": {"type": "string"}},
        "keep_ingredients": {"type": "array", "items": {"type": "string"}},
    },
}


class AddToCartArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: int = Field(ge=1)
    quantity: int = Field(ge=1, le=MAX_QUANTITY)
    units: int | None = Field(default=None, ge=0, le=500)
    option_ids: list[int] = Field(max_length=20)
    removed: list[str] = Field(max_length=20)
    keep_ingredients: list[str] = Field(max_length=20)


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
    quantity = args.quantity if args.units is None else packs_for(item, args.units)
    if isinstance(quantity, ToolError):
        return quantity
    new = NewLine(
        item_id=args.item_id,
        quantity=quantity,
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
    line = line_for(cart, new)
    return CartChange(
        action="added", quantity=quantity, line=line, left_out_for_dislikes=left_out, cart=cart
    )
