"""Which removable ingredients to leave out because the guest dislikes them.

Dislikes are soft and free text ("pickles"); matching is `menu/taste.mentions`, so
"mayo" matches "garlic mayo" and "onions" matches "onion". Leaving an ingredient
out never removes an allergen, so this never touches safety (`menu/configure.py`).
"""

from collections.abc import Iterable

from app.menu.taste import mentions


def disliked_removables(
    removable: Iterable[str], dislikes: Iterable[str], keep: Iterable[str]
) -> list[str]:
    """Removable ingredients that mention a dislike, except those the guest wants this time."""
    dislikes, keep = list(dislikes), list(keep)
    return [
        r
        for r in removable
        if any(mentions(r, d) for d in dislikes) and not any(mentions(r, k) for k in keep)
    ]
