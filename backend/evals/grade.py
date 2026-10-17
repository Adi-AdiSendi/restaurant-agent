"""Apply every check a case asks for to one run of it."""

from collections.abc import Awaitable, Callable, Mapping
from decimal import Decimal

from evals.case_model import Case
from evals.graders.cards import grade_turn
from evals.graders.memory import grade_profile
from evals.graders.prices import grade_prices
from evals.transcript import CaseRun, Check

JudgeFn = Callable[[str, str, str, str], Awaitable[Check]]
"""(criterion, user_text, reply, label) -> Check, see graders/judge.py."""


async def grade(
    case: Case, result: CaseRun, menu: Mapping[str, Decimal], judge: JudgeFn
) -> list[Check]:
    """`menu` maps each dish name to its price."""
    checks: list[Check] = []
    for number, (step, turn) in enumerate(zip(case.steps, result.turns, strict=True), start=1):
        label = f"turn {number}"
        checks += grade_turn(step.expect, turn, label)
        if turn.status != "ok":
            continue
        if step.expect.prices:
            said = [s.say for s in case.steps[:number] if s.user == step.user]
            checks.append(grade_prices(turn.reply, menu, said, label))
        if step.expect.judge:
            checks.append(await judge(step.expect.judge, step.say, turn.reply, label))
    for user, expected in case.profiles.items():
        checks += grade_profile(user, expected, result.profiles[user])
    return checks
