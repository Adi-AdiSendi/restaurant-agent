"""Soft notes from the guest's tastes: what they dislike, today's day rules, budget,
spice and calories left today. Never a block: allergies and diet are the hard rules
(`constraints.py`); these only hide dishes when the guest turns on "Matches my tastes".
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from app.menu.schemas import MenuItemBase

_WORD = re.compile(r"[a-z]+")


def _forms(word: str) -> set[str]:
    forms = {word}
    if word.endswith("es"):
        forms.add(word[:-2])
    if word.endswith("s"):
        forms.add(word[:-1])
    return forms


def mentions(text: str, phrase: str) -> bool:
    """The phrase's words appear in the text, in order and next to each other, ignoring
    case and a plural ending: "mayo" is in "garlic mayo", "onions" in "onion"."""
    have = [_forms(w) for w in _WORD.findall(text.lower())]
    want = [_forms(w) for w in _WORD.findall(phrase.lower())]
    if not want:
        return False
    return any(
        all(have[start + n] & word for n, word in enumerate(want))
        for start in range(len(have) - len(want) + 1)
    )


@dataclass(frozen=True)
class Tastes:
    dislikes: tuple[str, ...] = ()
    likes: tuple[str, ...] = ()
    today_avoid: tuple[str, ...] = ()
    """Foods from the guest's day rules for today, e.g. ("meat",) on a Friday."""
    today_want: tuple[str, ...] = ()
    """Foods the guest wants today from their day likes, e.g. ("fish",) on a Friday."""
    weekday: str = ""
    budget: Decimal | None = None
    max_spice: int | None = None
    kcal_left: int | None = None


NO_TASTES = Tastes()


def _has(item: MenuItemBase, food: str, removable: Iterable[str] = ()) -> bool:
    """The dish has this food and it cannot be left out. "meat" means not vegetarian."""
    if food == "meat":
        return not item.is_vegetarian
    stuck = [i for i in item.ingredients if i not in set(removable)]
    return mentions(item.name, food) or any(mentions(i, food) for i in stuck)


def taste_notes(item: MenuItemBase, tastes: Tastes) -> list[str]:
    notes = [
        f"has {d}, which you dislike" for d in tastes.dislikes if _has(item, d, item.removable)
    ]
    day = tastes.weekday.capitalize()
    notes += [f"you avoid {f} on {day}s" for f in tastes.today_avoid if _has(item, f)]
    if tastes.budget is not None and item.price_sar > tastes.budget:
        notes.append(f"over your {tastes.budget} SAR budget")
    if tastes.max_spice is not None and item.spice_level > tastes.max_spice:
        notes.append("spicier than you like")
    if tastes.kcal_left is not None and item.kcal is not None and item.kcal > tastes.kcal_left:
        notes.append(f"more than the {max(tastes.kcal_left, 0)} kcal left today")
    return notes


def liked(item: MenuItemBase, tastes: Tastes) -> bool:
    return any(_has(item, like) for like in tastes.likes)


def today_pick(item: MenuItemBase, tastes: Tastes) -> bool:
    """The dish has a food the guest wants on this weekday ("friday: fish")."""
    return any(_has(item, food) for food in tastes.today_want)
