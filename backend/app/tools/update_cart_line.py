"""update_cart_line: set how many of one cart line the guest wants."""

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.orders.cart import get_cart
from app.orders.cart_edit import set_quantity
from app.orders.errors import LineConflict
from app.orders.schemas import MAX_QUANTITY
from app.tools.cart_results import CartChange
from app.tools.cart_write import cart_write
from app.tools.context import ToolContext
from app.tools.errors import ToolError, invalid_arguments
from app.tools.order_errors import order_tool_error

NAME = "update_cart_line"

DESCRIPTION = """Set the quantity of one line in the guest's cart, when the guest asks \
("make that two").
Inputs: line_id (from the cart in your context, or view_cart) and quantity (1 to 20, \
the new total for that line, not an amount to add).
Example: {"line_id": 7, "quantity": 2}
Do NOT use it to change options or left-out ingredients (remove the line and add the \
dish again), or to remove a line (use remove_cart_line).
A line that breaks the guest's allergies or diet (added by hand, with their consent) \
can be lowered or removed but not raised: that returns error_category "conflict"."""

PARAMETERS: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["line_id", "quantity"],
    "properties": {"line_id": {"type": "integer"}, "quantity": {"type": "integer"}},
}


class UpdateCartLineArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    line_id: int = Field(ge=1)
    quantity: int = Field(ge=1, le=MAX_QUANTITY)


async def handle(arguments: str, context: ToolContext) -> CartChange | ToolError:
    try:
        args = UpdateCartLineArgs.model_validate_json(arguments)
    except ValidationError as exc:
        return invalid_arguments(exc)
    before = await get_cart(context.session, context.user_id, context.constraints)
    old = next((line for line in before.lines if line.id == args.line_id), None)
    if old and old.conflicts_with_guest and args.quantity > old.quantity:
        # The chat never adds more of a dish that breaks the guest's profile (ADR 0019).
        reasons = old.conflicts_with_guest
        message = f"{old.name} as chosen is not suitable: {', '.join(reasons)}."
        return order_tool_error(LineConflict(message, reasons))
    cart = await cart_write(
        context,
        lambda: set_quantity(
            context.session, context.user_id, args.line_id, args.quantity, context.constraints
        ),
    )
    if isinstance(cart, ToolError):
        return cart
    line = next((line for line in cart.lines if line.id == args.line_id), None)
    return CartChange(action="updated", quantity=args.quantity, line=line, cart=cart)
