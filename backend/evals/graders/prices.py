"""Every price the reply states must be the real price of the dish it is attached to.

A price is attached to the last menu item named before it in the same sentence.
A price with no dish named before it must still be a menu price, or a number
the user said (a budget like "under 30 SAR" is often echoed back).
"""

import re
from collections.abc import Iterable, Mapping
from decimal import Decimal

from app.menu.restaurant_schemas import RestaurantFile
from evals.transcript import Check

# "85 SAR", "85.00 SAR", "SAR 85", "SAR85". A range "16-22 SAR" yields only 22.
_PRICE = re.compile(r"(\d+(?:\.\d{1,2})?)\s*SAR\b|\bSAR\s*(\d+(?:\.\d{1,2})?)", re.IGNORECASE)
_NUMBER = re.compile(r"\d+(?:\.\d{1,2})?")
_SENTENCE_END = re.compile(r"[.!?;\n](?:\s|$)")


def stated_prices(text: str) -> list[Decimal]:
    return [Decimal(a or b) for a, b in _PRICE.findall(text)]


def _dish_before(text: str, end: int, names: Iterable[str]) -> str | None:
    starts = [m.end() for m in _SENTENCE_END.finditer(text, 0, end)]
    sentence = text[starts[-1] if starts else 0 : end].lower()
    found = [(sentence.rfind(n.lower()), n) for n in names if n.lower() in sentence]
    return max(found)[1] if found else None


def grade_prices(
    reply: str, menu: Mapping[str, Decimal], user_texts: Iterable[str], label: str
) -> Check:
    allowed = set(menu.values()) | {Decimal(n) for t in user_texts for n in _NUMBER.findall(t)}
    wrong: list[str] = []
    for match in _PRICE.finditer(reply):
        price = Decimal(match.group(1) or match.group(2))
        dish = _dish_before(reply, match.start(), menu)
        if dish is not None and price != menu[dish]:
            wrong.append(f"{dish} {price} (menu {menu[dish]})")
        elif dish is None and price not in allowed:
            wrong.append(str(price))
    return Check(name=f"{label} prices", passed=not wrong, detail=", ".join(wrong))


def prices_by_restaurant(
    restaurants: Iterable[RestaurantFile], needed: Iterable[str]
) -> dict[str, dict[str, Decimal]]:
    """Dish name -> price for each restaurant slug; names repeat across restaurants."""
    prices = {r.slug: {item.name: item.price_sar for item in r.items} for r in restaurants}
    unknown = sorted(set(needed) - set(prices))
    if unknown:
        raise ValueError(f"Cases name restaurants with no data file: {unknown}")
    return prices
