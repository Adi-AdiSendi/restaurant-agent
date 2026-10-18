"""Which removable ingredients to leave out because the guest dislikes them.

Dislikes are soft and free text ("pickles"), so matching ignores case and a plural
ending, and finds the dislike's words anywhere in the ingredient: "mayo" matches
"garlic mayo" and "slaw (mayo)". Leaving an ingredient out never removes an
allergen, so this never touches safety (`menu/configure.py`).
"""

import re
from collections.abc import Iterable

_WORD = re.compile(r"[a-z]+")


def _forms(word: str) -> set[str]:
    forms = {word}
    if word.endswith("es"):
        forms.add(word[:-2])
    if word.endswith("s"):
        forms.add(word[:-1])
    return forms


def _words(text: str) -> list[set[str]]:
    return [_forms(w) for w in _WORD.findall(text.lower())]


def _mentions(ingredient: str, phrase: str) -> bool:
    """The phrase's words appear in the ingredient, in order and next to each other."""
    have, want = _words(ingredient), _words(phrase)
    if not want:
        return False
    return any(
        all(have[start + n] & word for n, word in enumerate(want))
        for start in range(len(have) - len(want) + 1)
    )


def disliked_removables(
    removable: Iterable[str], dislikes: Iterable[str], keep: Iterable[str]
) -> list[str]:
    """Removable ingredients that mention a dislike, except those the guest wants this time."""
    dislikes, keep = list(dislikes), list(keep)
    return [
        r
        for r in removable
        if any(_mentions(r, d) for d in dislikes) and not any(_mentions(r, k) for k in keep)
    ]
