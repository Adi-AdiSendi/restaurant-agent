"""Turn a cart or order error into the tool error shape, saying what the model should do."""

from app.orders.errors import OrderError, OtherRestaurant
from app.tools.errors import ErrorCategory, ToolError

_CATEGORIES: dict[str, ErrorCategory] = {
    "not_found": "not_found",
    "invalid_choice": "invalid_choice",
    "conflict": "conflict",
    "other_restaurant": "other_restaurant",
    "empty_cart": "empty_cart",
    "unavailable": "unavailable",
}

_ADVICE: dict[str, str] = {
    "invalid_choice": "Check the item's option groups and removable ingredients with get_item.",
    "conflict": "Tell the guest why it does not suit them and suggest something that does. "
    "Never offer to add it anyway: the chat cannot override their allergies or diet.",
    "other_restaurant": "Tell the guest their cart holds dishes from {restaurant}. They can "
    'empty it with the "Empty cart" button in their cart, then ask again. You cannot empty it.',
    "empty_cart": "The cart is empty. Offer to add something first.",
    "unavailable": "Some lines are no longer on the menu. Ask the guest to remove them first.",
}


def order_tool_error(exc: OrderError) -> ToolError:
    """Order errors are not retryable: the same call would be refused again."""
    restaurant = exc.restaurant if isinstance(exc, OtherRestaurant) else ""
    advice = _ADVICE.get(exc.code, "").format(restaurant=restaurant)
    return ToolError(
        error_category=_CATEGORIES.get(exc.code, "invalid_choice"),
        retryable=False,
        message=f"{exc.message} {advice}".strip(),
    )
