"""The small LLM interface the agent loop depends on. Tests inject a fake."""

from dataclasses import dataclass, field
from typing import Protocol

from app.memory.extract import JSONCompleter

# Responses API input items and tool/format specs, as plain JSON-like dicts.
InputItem = dict[str, object]
Spec = dict[str, object]


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    name: str
    arguments: str


@dataclass(frozen=True)
class ModelTurn:
    """One model response.

    `replay_items` are the response's own output items (reasoning and function
    calls) to send back before the tool outputs. With `store=False` this is how
    a reasoning model keeps its reasoning between tool rounds.
    """

    output_text: str
    tool_calls: list[ToolCall] = field(default_factory=list[ToolCall])
    replay_items: list[InputItem] = field(default_factory=list[InputItem])


class LLMClient(Protocol):
    async def respond(
        self,
        *,
        instructions: str,
        input_items: list[InputItem],
        tools: list[Spec],
        text_format: Spec,
    ) -> ModelTurn: ...


class AgentLLM(LLMClient, JSONCompleter, Protocol):
    """What one chat turn needs: the tool loop and the memory extraction call."""


class LLMUnavailableError(Exception):
    """The provider could not be reached, refused the request, or is not configured."""
