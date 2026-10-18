"""remove_cart_line: take one line out of the guest's cart."""

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.orders.cart import get_cart
from app.orders.cart_edit import remove_line
from app.tools.cart_results import CartChange
from app.tools.cart_write import cart_write
from app.tools.context import ToolContext
from app.tools.errors import ToolError, invalid_arguments

NAME = "remove_cart_line"

DESCRIPTION = """Remove one line from the guest's cart, when the guest asks.
Input: line_id, from the cart in your context or view_cart.
Example: {"line_id": 7}
Do NOT use it to lower a quantity (use update_cart_line), or to empty the whole \
cart (use clear_cart)."""

PARAMETERS: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["line_id"],
    "properties": {"line_id": {"type": "integer"}},
}


class RemoveCartLineArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    line_id: int = Field(ge=1)


async def handle(arguments: str, context: ToolContext) -> CartChange | ToolError:
    try:
        args = RemoveCartLineArgs.model_validate_json(arguments)
    except ValidationError as exc:
        return invalid_arguments(exc)
    before = await get_cart(context.session, context.user_id, context.constraints)
    old = next((line for line in before.lines if line.id == args.line_id), None)
    cart = await cart_write(
        context,
        lambda: remove_line(context.session, context.user_id, args.line_id, context.constraints),
    )
    if isinstance(cart, ToolError):
        return cart
    quantity = old.quantity if old else 0
    return CartChange(action="removed", quantity=quantity, line=old, cart=cart)
