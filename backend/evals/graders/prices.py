"""Every price the reply states must be a real menu price (or a number the user said)."""

import re
from collections.abc import Iterable
from decimal import Decimal

from evals.transcript import Check

# "85 SAR", "85.00 SAR", "SAR 85", "SAR85". Thousands separators are not expected here.
_PRICE = re.compile(r"(\d+(?:\.\d{1,2})?)\s*SAR\b|\bSAR\s*(\d+(?:\.\d{1,2})?)", re.IGNORECASE)
_NUMBER = re.compile(r"\d+(?:\.\d{1,2})?")


def stated_prices(text: str) -> list[Decimal]:
    return [Decimal(a or b) for a, b in _PRICE.findall(text)]


def grade_prices(
    reply: str, menu_prices: Iterable[Decimal], user_texts: Iterable[str], label: str
) -> Check:
    """A budget the user gave ("under 30 SAR") may be echoed back, so it is allowed."""
    allowed = set(menu_prices) | {Decimal(n) for t in user_texts for n in _NUMBER.findall(t)}
    invented = sorted({p for p in stated_prices(reply) if p not in allowed})
    return Check(name=f"{label} prices", passed=not invented, detail=", ".join(map(str, invented)))
