"""Turn a user message into validated memory operations (one structured LLM call).

The call goes through an injected `JSONCompleter`, implemented in `agent/`, so
this module never imports the SDK and tests can script the answer.
"""

import logging
from collections.abc import Sequence
from typing import Protocol

from pydantic import BaseModel, ValidationError

from app.memory.extract_prompt import EXTRACTION_FORMAT, EXTRACTION_PROMPT
from app.memory.operations import Operation
from app.memory.preference import Preference

logger = logging.getLogger(__name__)


class _RawExtraction(BaseModel):
    operations: list[dict[str, object]]


class JSONCompleter(Protocol):
    async def complete_json(
        self, *, instructions: str, user_input: str, text_format: dict[str, object]
    ) -> str: ...


def render_input(
    profile: Sequence[Preference], previous_assistant: str | None, message: str
) -> str:
    facts = "\n".join(f"- {p.id}: {p.kind} = {p.value}" for p in profile) or "- (empty)"
    asked = previous_assistant or "(none, this is the first message)"
    return (
        f"Current profile:\n{facts}\n\n"
        f"Previous assistant message:\n{asked}\n\n"
        f"New guest message:\n{message}"
    )


async def extract_operations(
    llm: JSONCompleter,
    profile: Sequence[Preference],
    previous_assistant: str | None,
    message: str,
) -> list[Operation]:
    """Invalid JSON means no change; an invalid operation is dropped, the rest kept."""
    text = await llm.complete_json(
        instructions=EXTRACTION_PROMPT,
        user_input=render_input(profile, previous_assistant, message),
        text_format=EXTRACTION_FORMAT,
    )
    try:
        raw = _RawExtraction.model_validate_json(text)
    except ValidationError:
        logger.warning("memory_extraction_invalid")
        return []
    ops: list[Operation] = []
    for item in raw.operations:
        try:
            ops.append(Operation.model_validate(item))
        except ValidationError as exc:
            logger.warning("memory_operation_dropped errors=%d", exc.error_count())
    return ops
