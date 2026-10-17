"""What one run of one case produced, and how it was graded. Saved as JSON."""

from typing import Literal

from pydantic import BaseModel, Field

from app.agent.schemas import Card

TurnStatus = Literal["ok", "timeout", "refused", "error"]


class Turn(BaseModel):
    user: str
    say: str
    status: TurnStatus
    seconds: float
    reply: str = ""
    cards: list[Card] = Field(default_factory=list[Card])
    error: str | None = None


class StoredFact(BaseModel):
    kind: str
    value: str
    status: str


class Check(BaseModel):
    name: str
    passed: bool
    detail: str = ""


class CaseRun(BaseModel):
    case_id: str
    category: str
    run: int
    turns: list[Turn]
    profiles: dict[str, list[StoredFact]]
    checks: list[Check] = Field(default_factory=list[Check])

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)
