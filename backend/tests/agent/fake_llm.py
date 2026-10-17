"""A scripted LLMClient. Unit tests never call the real model."""

import asyncio
import copy
import json
from dataclasses import dataclass, field

from app.agent.llm_client import InputItem, ModelTurn, Spec, ToolCall


@dataclass
class FakeLLM:
    """Scripted chat turns plus scripted extraction answers (default: no memory ops)."""

    turns: list[ModelTurn]
    error: Exception | None = None
    extractions: list[str] = field(default_factory=list[str])
    calls: list[list[InputItem]] = field(default_factory=list[list[InputItem]])
    extraction_inputs: list[str] = field(default_factory=list[str])
    respond_delay: float = 0.0

    async def complete_json(
        self, *, instructions: str, user_input: str, text_format: dict[str, object]
    ) -> str:
        self.extraction_inputs.append(user_input)
        if self.error:
            raise self.error
        return self.extractions.pop(0) if self.extractions else '{"operations": []}'

    async def respond(
        self,
        *,
        instructions: str,
        input_items: list[InputItem],
        tools: list[Spec],
        text_format: Spec,
    ) -> ModelTurn:
        self.calls.append(copy.deepcopy(input_items))
        await asyncio.sleep(self.respond_delay)
        if self.error:
            raise self.error
        if not self.turns:
            raise AssertionError("FakeLLM ran out of scripted turns")
        return self.turns.pop(0)


def tool_turn(
    name: str,
    arguments: dict[str, object],
    call_id: str = "call_1",
    reasoning: InputItem | None = None,
) -> ModelTurn:
    """A turn with one tool call, replaying items the way the OpenAI adapter does."""
    args = json.dumps(arguments)
    replay: list[InputItem] = [reasoning] if reasoning else []
    replay.append({"type": "function_call", "call_id": call_id, "name": name, "arguments": args})
    return ModelTurn(
        output_text="", tool_calls=[ToolCall(call_id, name, args)], replay_items=replay
    )


def extraction(*ops: dict[str, object]) -> str:
    """A scripted extraction answer, e.g. extraction(op("add", "diet", "vegan"))."""
    return json.dumps({"operations": list(ops)})


def op(action: str, kind: str, value: str, target_id: int | None = None) -> dict[str, object]:
    return {"op": action, "kind": kind, "value": value, "target_id": target_id}


def answer_turn(reply: str, item_ids: list[int]) -> ModelTurn:
    return ModelTurn(output_text=json.dumps({"reply": reply, "recommended_item_ids": item_ids}))


EMPTY_SEARCH: dict[str, object] = {
    "category": None,
    "max_price_sar": None,
    "max_spice": None,
    "vegetarian": False,
    "vegan": False,
    "exclude_allergens": [],
    "text": None,
}
