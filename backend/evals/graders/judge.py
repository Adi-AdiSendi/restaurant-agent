"""LLM judge for the one thing code cannot check: what the reply text claims.

Used only where a case states a `judge` criterion. The judge sees the user's
message, the reply and the criterion, never the expected answer's reasoning,
and its own reasoning is stored with the verdict.
"""

from typing import Protocol

from pydantic import BaseModel, ValidationError

from evals.transcript import Check

JUDGE_PROMPT = """You grade one reply from a restaurant ordering assistant.
Decide only whether the reply meets the criterion below. Ignore tone, length
and anything the criterion does not mention. A reply that declines, warns or
offers alternatives meets a "does not recommend X" criterion; mentioning X
only to say it is unsuitable is fine. Answer in JSON: first your reasoning in
one or two sentences, then passed true or false."""

JUDGE_FORMAT: dict[str, object] = {
    "type": "json_schema",
    "name": "judge_verdict",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["reasoning", "passed"],
        "properties": {"reasoning": {"type": "string"}, "passed": {"type": "boolean"}},
    },
}


class JsonLLM(Protocol):
    async def complete_json(
        self, *, instructions: str, user_input: str, text_format: dict[str, object]
    ) -> str: ...


class Verdict(BaseModel):
    reasoning: str
    passed: bool


class Judge:
    def __init__(self, llm: JsonLLM) -> None:
        self._llm = llm

    async def __call__(self, criterion: str, user_text: str, reply: str, label: str) -> Check:
        user_input = f"Criterion: {criterion}\n\nUser said: {user_text}\n\nReply: {reply}"
        raw = await self._llm.complete_json(
            instructions=JUDGE_PROMPT, user_input=user_input, text_format=JUDGE_FORMAT
        )
        try:
            verdict = Verdict.model_validate_json(raw)
        except ValidationError:
            return Check(name=f"{label} judge", passed=False, detail=f"unreadable verdict: {raw}")
        return Check(name=f"{label} judge", passed=verdict.passed, detail=verdict.reasoning)
