"""Dishes sold in packs (a box of 3 dates): a count that is not whole packs is not added.

The guest must choose the nearest whole number of packs first, so the chat asks
before anything goes in the cart. Enforced here, not only in the prompt.
"""

from app.menu.schemas import MenuItemBase
from app.tools.errors import ToolError


def packs_for(item: MenuItemBase, units: int) -> int | ToolError:
    """The number of packs for `units` pieces, or an error naming the nearest counts."""
    size, unit = item.pack_size, item.pack_unit or "pieces"
    if units < 1:
        message = f"Ask how many {unit} the guest wants."
        return ToolError(error_category="invalid_arguments", retryable=False, message=message)
    if units % size == 0:
        return units // size
    lower, upper = units // size * size, (units // size + 1) * size

    def count(n: int) -> str:
        packs = n // size
        return f"{n} ({packs} {'pack' if packs == 1 else 'packs'})"

    nearest = count(upper) if lower == 0 else f"{count(upper)} or {count(lower)}"
    return ToolError(
        error_category="needs_confirmation",
        retryable=False,
        message=(
            f"{item.name} comes in packs of {size} {unit}, so {units} is not possible. "
            f"The nearest is {nearest}. Tell the guest and ask which they want; add only "
            "after they agree, with units set to that number."
        ),
    )
