"""Deterministic checks on the speaker's cart and orders after a turn (no LLM)."""

from app.orders.schemas import CartLineOut
from evals.expectations import Expect, LineExpect
from evals.transcript import Check, Turn


def _matches(want: LineExpect, line: CartLineOut) -> bool:
    if (want.name, want.quantity) != (line.name, line.quantity):
        return False
    if want.options is not None and sorted(want.options) != sorted(o.name for o in line.options):
        return False
    return want.removed is None or sorted(want.removed) == sorted(line.removed)


def _describe(line: CartLineOut) -> str:
    details = [o.name for o in line.options] + [f"no {r}" for r in line.removed]
    return f"{line.quantity} x {line.name} ({', '.join(details)})"


def _cart(expected: list[LineExpect], turn: Turn, label: str) -> Check:
    """Exactly the expected lines: each matches a different line, and nothing is left over."""
    lines = list(turn.cart.lines) if turn.cart else []
    unmatched = list(lines)
    missing: list[str] = []
    for want in expected:
        found = next((line for line in unmatched if _matches(want, line)), None)
        if found is None:
            missing.append(want.name)
        else:
            unmatched.remove(found)
    passed = not missing and not unmatched
    detail = "; ".join(_describe(line) for line in lines) or "empty"
    if missing:
        detail = f"missing {missing}; cart: {detail}"
    return Check(name=f"{label} cart", passed=passed, detail=detail)


def grade_cart(expect: Expect, turn: Turn, label: str) -> list[Check]:
    checks: list[Check] = []
    if expect.cart is not None:
        checks.append(_cart(expect.cart, turn, label))
    if expect.orders is not None:
        ok = turn.orders == expect.orders
        checks.append(Check(name=f"{label} orders", passed=ok, detail=str(turn.orders)))
    if expect.checkout_card is not None:
        shown = "checkout" in turn.actions
        name = f"{label} checkout card {'shown' if expect.checkout_card else 'not shown'}"
        ok = shown == expect.checkout_card
        checks.append(Check(name=name, passed=ok, detail=str(turn.actions)))
    return checks
