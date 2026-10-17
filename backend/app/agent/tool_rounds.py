"""Call the model and run its tools until it gives a valid structured answer."""

import logging
from dataclasses import dataclass, field

from pydantic import ValidationError

from app.agent.answer import TEXT_FORMAT, FinalAnswer, retry_instruction
from app.agent.errors import AgentAnswerError, AgentLoopError
from app.agent.grounding import ids_in_tool_result
from app.agent.llm_client import InputItem, LLMClient
from app.agent.tool_dispatch import TOOL_SPECS, run_tool
from app.tools.context import ToolContext

MAX_TOOL_ROUNDS = 5
RETRY_TOOL_ROUNDS = 1
logger = logging.getLogger(__name__)


@dataclass
class Turn:
    client: LLMClient
    context: ToolContext
    instructions: str
    items: list[InputItem]
    seen_ids: set[int] = field(default_factory=set[int])


async def final_answer(turn: Turn, max_tool_rounds: int) -> FinalAnswer:
    """Validate the answer; on failure, retry once with the validation error."""
    text = await _run_until_answer(turn, max_tool_rounds)
    try:
        return FinalAnswer.model_validate_json(text)
    except ValidationError as exc:
        logger.warning("agent_answer_invalid errors=%d", exc.error_count())
        turn.items.append({"role": "assistant", "content": text})
        turn.items.append({"role": "developer", "content": retry_instruction(exc)})
    text = await _run_until_answer(turn, RETRY_TOOL_ROUNDS)
    try:
        return FinalAnswer.model_validate_json(text)
    except ValidationError as exc:
        raise AgentAnswerError(f"Final answer invalid after retry: {exc}") from exc


async def _run_until_answer(turn: Turn, max_tool_rounds: int) -> str:
    """Call the model, running its tool calls, until it answers without tools."""
    for round_number in range(max_tool_rounds + 1):
        response = await turn.client.respond(
            instructions=turn.instructions,
            input_items=turn.items,
            tools=TOOL_SPECS,
            text_format=TEXT_FORMAT,
        )
        if not response.tool_calls:
            return response.output_text
        if round_number == max_tool_rounds:
            break
        turn.items.extend(response.replay_items)
        for call in response.tool_calls:
            result = await run_tool(call, turn.context)
            logger.info("agent_tool_call name=%s", call.name)
            turn.seen_ids |= ids_in_tool_result(result)
            output = result.model_dump_json()
            turn.items.append(
                {"type": "function_call_output", "call_id": call.call_id, "output": output}
            )
    raise AgentLoopError(f"Model still calling tools after {max_tool_rounds} rounds")
