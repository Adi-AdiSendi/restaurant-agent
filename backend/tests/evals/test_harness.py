"""Harness, judge and report with the fake LLM. No real model calls."""

from typing import Any

from sqlalchemy import func, select

from app.agent.llm_client import LLMUnavailableError
from app.db.engine import get_sessionmaker
from app.users.models import User
from evals.case_model import Case
from evals.grade import grade
from evals.graders.judge import Judge
from evals.harness import run_case
from evals.report import summarize
from evals.run import crashed
from evals.transcript import CaseRun, Check
from tests.agent.fake_llm import FakeLLM, answer_turn


def case(**fields: Any) -> Case:
    base: dict[str, Any] = {"id": "c", "category": "isolation", "description": "d"}
    return Case.model_validate(base | fields)


async def eval_users_left() -> int:
    async with get_sessionmaker()() as session:
        stmt = select(func.count()).where(User.username.like("ev900_%"))
        return await session.scalar(stmt) or 0


async def test_run_records_turns_refusals_and_leaves_nothing_behind() -> None:
    two_users = case(
        users=["alice", "bob"],
        steps=[
            {"user": "alice", "say": "hi"},
            {"user": "bob", "say": "what did she say?", "into_conversation_of": "alice"},
        ],
    )
    result = await run_case(two_users, 900, 1, FakeLLM([answer_turn("Hello", [])]), 5.0)
    assert [(t.status, t.reply) for t in result.turns] == [("ok", "Hello"), ("refused", "")]
    assert result.profiles == {"alice": [], "bob": []}
    assert await eval_users_left() == 0


async def test_a_slow_turn_is_a_timeout_and_later_turns_still_run() -> None:
    llm = FakeLLM([answer_turn("late", []), answer_turn("on time", [])], respond_delay=0.3)
    steps = [{"user": "u", "say": "one"}, {"user": "u", "say": "two"}]
    result = await run_case(case(users=["u"], steps=steps), 900, 2, llm, 0.1)
    assert [t.status for t in result.turns] == ["timeout", "timeout"]
    llm.respond_delay = 0
    result = await run_case(case(users=["u"], steps=steps), 900, 3, llm, 5.0)
    assert [t.status for t in result.turns] == ["ok", "ok"]


async def test_judge_verdicts_and_grading() -> None:
    yes = '{"reasoning": "It declined.", "passed": true}'
    judge = Judge(FakeLLM([], extractions=[yes, "not json"]))
    assert await judge("crit", "q", "reply", "turn 1") == Check(
        name="turn 1 judge", passed=True, detail="It declined."
    )
    unreadable = await judge("crit", "q", "reply", "turn 1")
    assert not unreadable.passed

    judged = case(users=["u"], steps=[{"user": "u", "say": "q", "expect": {"judge": "crit"}}])
    run = CaseRun.model_validate(
        {
            "case_id": "c",
            "category": "isolation",
            "run": 1,
            "turns": [{"user": "u", "say": "q", "status": "ok", "seconds": 1, "reply": "r"}],
            "profiles": {"u": []},
        }
    )
    checks = await grade(judged, run, {}, Judge(FakeLLM([], extractions=[yes])))
    assert [(c.name, c.passed) for c in checks] == [("turn 1 status", True), ("turn 1 judge", True)]


def test_a_safety_case_must_pass_every_run() -> None:
    def run(number: int, passed: bool) -> CaseRun:
        check = Check(name="x", passed=passed)
        return CaseRun(
            case_id="c", category="isolation", run=number, turns=[], profiles={}, checks=[check]
        )

    [row] = summarize([run(1, True), run(2, True), run(3, False)])
    assert (row.safety, row.cases_passed, row.runs_passed, row.runs) == (True, 0, 2, 3)


async def test_an_unavailable_judge_fails_the_check() -> None:
    judge = Judge(FakeLLM([], error=LLMUnavailableError("RateLimitError")))
    check = await judge("crit", "q", "reply", "turn 1")
    assert (check.passed, check.detail) == (False, "judge unavailable: RateLimitError")


def test_a_crashed_case_is_kept_as_a_failure() -> None:
    result = crashed(case(users=["u"], steps=[{"user": "u", "say": "q"}]), 2, KeyError("x"))
    assert (result.run, result.passed, result.checks[0].detail) == (2, False, "KeyError: 'x'")


def test_dead_ends_count_answered_turns_without_card_or_question() -> None:
    turns = [
        {"user": "u", "say": "q", "status": "ok", "seconds": 1, "reply": "Noted."},
        {"user": "u", "say": "q", "status": "ok", "seconds": 1, "reply": "What now?"},
        {"user": "u", "say": "q", "status": "timeout", "seconds": 1},
    ]
    result = CaseRun.model_validate(
        {"case_id": "c", "category": "grounding", "run": 1, "turns": turns, "profiles": {}}
    )
    [row] = summarize([result])
    assert (row.dead_ends, row.answered) == (1, 2)
