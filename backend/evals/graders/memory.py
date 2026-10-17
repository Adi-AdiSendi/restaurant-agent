"""Deterministic checks on what each user's profile holds at the end of a case."""

from evals.case_model import Fact, ProfileExpect
from evals.transcript import Check, StoredFact


def grade_profile(user: str, expect: ProfileExpect, stored: list[StoredFact]) -> list[Check]:
    def with_status(status: str) -> set[tuple[str, str]]:
        return {(f.kind, f.value) for f in stored if f.status == status}

    active, superseded = with_status("active"), with_status("superseded")
    checks: list[Check] = []

    def check(name: str, wanted: list[Fact], have: set[tuple[str, str]], present: bool) -> None:
        missing = [f"{k}={v}" for k, v in wanted if ((str(k), v) in have) != present]
        checks.append(Check(name=f"{user} {name}", passed=not missing, detail=", ".join(missing)))

    if expect.active:
        check("active", expect.active, active, present=True)
    if expect.superseded:
        check("superseded", expect.superseded, superseded, present=True)
    if expect.not_active:
        check("not active", expect.not_active, active, present=False)
    if expect.exact:
        extra = sorted(active - {(str(k), v) for k, v in expect.active})
        detail = ", ".join(f"{k}={v}" for k, v in extra)
        checks.append(Check(name=f"{user} nothing else active", passed=not extra, detail=detail))
    return checks
