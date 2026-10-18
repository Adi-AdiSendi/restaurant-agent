"""Which removable ingredients to leave out because the guest dislikes them.

Dislikes are soft and free text ("pickles"), so matching ignores case, spacing and
a plural ending. Leaving an ingredient out never removes an allergen, so this
never touches safety (`menu/configure.py`).
"""

from collections.abc import Iterable


def _forms(word: str) -> set[str]:
    w = " ".join(word.lower().split())
    forms = {w}
    if w.endswith("es"):
        forms.add(w[:-2])
    if w.endswith("s"):
        forms.add(w[:-1])
    return forms


def _matches(ingredient: str, words: Iterable[str]) -> bool:
    forms = _forms(ingredient)
    return any(forms & _forms(word) for word in words)


def disliked_removables(
    removable: Iterable[str], dislikes: Iterable[str], keep: Iterable[str]
) -> list[str]:
    """Removable ingredients that match a dislike, except those the guest wants this time."""
    dislikes, keep = list(dislikes), list(keep)
    return [r for r in removable if _matches(r, dislikes) and not _matches(r, keep)]
