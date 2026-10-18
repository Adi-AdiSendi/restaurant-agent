"""Per-category results. Never a single overall number (see .claude/rules/evals.md)."""

import math
from collections import defaultdict

from pydantic import BaseModel

from evals.case_model import SAFETY_CATEGORIES
from evals.transcript import CaseRun


class CategoryRow(BaseModel):
    category: str
    safety: bool
    cases: int
    cases_passed: int
    """Cases that passed in every run: the worst-run view, used for safety."""
    runs: int
    runs_passed: int
    timeouts: int
    errors: int
    dead_ends: int
    """Answered turns with no card and no question: the guest is left with nothing to do.
    Reported, not graded (added after the phase 7 review found the note suppressing them)."""
    answered: int
    p95_seconds: float
    """95th percentile turn time, against the 22 s deadline."""


def p95(seconds: list[float]) -> float:
    ordered = sorted(seconds)
    return ordered[max(math.ceil(0.95 * len(ordered)) - 1, 0)] if ordered else 0.0


def summarize(results: list[CaseRun]) -> list[CategoryRow]:
    by_category: dict[str, dict[str, list[CaseRun]]] = defaultdict(lambda: defaultdict(list))
    for result in results:
        by_category[result.category][result.case_id].append(result)
    rows: list[CategoryRow] = []
    for category, cases in sorted(by_category.items()):
        runs = [r for case_runs in cases.values() for r in case_runs]
        statuses = [t.status for r in runs for t in r.turns]
        answered = [t for r in runs for t in r.turns if t.status == "ok"]
        rows.append(
            CategoryRow(
                category=category,
                safety=category in SAFETY_CATEGORIES,
                cases=len(cases),
                cases_passed=sum(all(r.passed for r in rs) for rs in cases.values()),
                runs=len(runs),
                runs_passed=sum(r.passed for r in runs),
                timeouts=statuses.count("timeout"),
                errors=statuses.count("error"),
                dead_ends=sum(not t.cards and "?" not in t.reply for t in answered),
                answered=len(answered),
                p95_seconds=p95([t.seconds for r in runs for t in r.turns]),
            )
        )
    return rows


def table(rows: list[CategoryRow]) -> str:
    lines = [
        "| Category | Cases passed (all runs) | Runs passed | Timeouts | Errors | Dead ends "
        "| p95 turn |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        name = f"{r.category} (safety)" if r.safety else r.category
        lines.append(
            f"| {name} | {r.cases_passed}/{r.cases} | {r.runs_passed}/{r.runs} "
            f"| {r.timeouts} | {r.errors} | {r.dead_ends}/{r.answered} | {r.p95_seconds:.1f} s |"
        )
    return "\n".join(lines)
