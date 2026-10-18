"""The guest's cart at the start of a turn, as a developer note for the model.

It gives each line's id, so "make that two" or "drop the fries" can name the
right line without a tool call. Tool results show any change made this turn.
"""

from app.orders.schemas import CartLineOut, CartOut


def _line(line: CartLineOut) -> str:
    details = [o.name for o in line.options] + [f"no {r}" for r in line.removed]
    text = f"- line_id {line.id}: {line.quantity} x {line.name}"
    if details:
        text += f" ({', '.join(details)})"
    if line.line_total_sar is not None:
        text += f", {line.line_total_sar} SAR"
    if line.problem:
        text += f". Cannot be ordered: {line.problem}"
    return text


def cart_block(cart: CartOut, restaurant_slug: str) -> str:
    if cart.restaurant is None or not cart.lines:
        return "The guest's cart is empty."
    elsewhere = (
        ""
        if cart.restaurant.slug == restaurant_slug
        else " It is from another restaurant: nothing from here can be added until the "
        'guest empties it with the "Empty cart" button in their cart.'
    )
    lines = "\n".join(_line(line) for line in cart.lines)
    return (
        f"The guest's cart, from {cart.restaurant.name}, total {cart.total_sar} SAR."
        f"{elsewhere}\n{lines}\n"
        "Use these line_id values with update_cart_line and remove_cart_line."
    )
