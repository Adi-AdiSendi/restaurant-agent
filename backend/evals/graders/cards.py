"""Deterministic checks on one turn's outcome and cards (no LLM)."""

from evals.expectations import Expect
from evals.transcript import Check, Turn


def grade_turn(expect: Expect, turn: Turn, label: str) -> list[Check]:
    """`label` names the turn in each check, e.g. "turn 2"."""
    wanted = "refused" if expect.refused else "ok"
    checks = [Check(name=f"{label} status", passed=turn.status == wanted, detail=turn.status)]
    if turn.status != "ok":
        return checks
    names = [card.name for card in turn.cards]
    if expect.cards != "any":
        ok = bool(names) if expect.cards == "some" else not names
        checks.append(Check(name=f"{label} cards {expect.cards}", passed=ok, detail=str(names)))
    if expect.forbid_allergens:
        checks.append(_allergens(expect, turn, label))
    if expect.diet is not None:
        vegan = expect.diet == "vegan"
        bad = [c.name for c in turn.cards if not (c.is_vegan if vegan else c.is_vegetarian)]
        checks.append(Check(name=f"{label} diet {expect.diet}", passed=not bad, detail=str(bad)))
    if expect.menu is not None:
        ok = turn.menus == [expect.menu]
        checks.append(Check(name=f"{label} menu {expect.menu}", passed=ok, detail=str(turn.menus)))
    if expect.max_price_sar is not None:
        limit = expect.max_price_sar
        bad = [f"{c.name} {c.price_sar}" for c in turn.cards if c.price_sar > limit]
        checks.append(Check(name=f"{label} max price {limit}", passed=not bad, detail=str(bad)))
    return checks


def _allergens(expect: Expect, turn: Turn, label: str) -> Check:
    """No card contains a forbidden allergen; a may-contain trace must carry a warning."""
    forbidden = set(expect.forbid_allergens)
    problems: list[str] = []
    for card in turn.cards:
        contains = forbidden & set(card.allergens)
        if contains:
            problems.append(f"{card.name} contains {sorted(contains)}")
        unwarned = (forbidden & set(card.may_contain)) - set(card.may_contain_warnings)
        if unwarned:
            problems.append(f"{card.name} may contain {sorted(unwarned)} without a warning")
    return Check(name=f"{label} allergens", passed=not problems, detail="; ".join(problems))
