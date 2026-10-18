"""Domain errors for carts and orders. The API turns each into a status and a `code`."""


class OrderError(Exception):
    code = "order_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFound(OrderError):
    """No such restaurant, item, cart line or order for this user."""

    code = "not_found"


class InvalidChoice(OrderError):
    """The options, removals or quantity do not make a valid order of the item."""

    code = "invalid_choice"


class LineConflict(OrderError):
    """The choice breaks the guest's saved allergies or diet; it needs their acknowledgement."""

    code = "conflict"

    def __init__(self, message: str, reasons: list[str]) -> None:
        super().__init__(message)
        self.reasons = reasons


class OtherRestaurant(OrderError):
    """The cart holds items from another restaurant; replacing it needs the guest's consent."""

    code = "other_restaurant"

    def __init__(self, message: str, restaurant: str) -> None:
        super().__init__(message)
        self.restaurant = restaurant


class EmptyCart(OrderError):
    code = "empty_cart"


class UnavailableLines(OrderError):
    """A line's item or options changed on the menu; it must be removed before checkout."""

    code = "unavailable"


class CartChanged(OrderError):
    """The total is not the one the guest reviewed: a chat turn or another tab changed it."""

    code = "cart_changed"
