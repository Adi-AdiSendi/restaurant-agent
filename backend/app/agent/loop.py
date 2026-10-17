"""One chat turn: model answer, grounded cards, and the safety post-check.

Every card passes `safety.check` against the guest's hard constraints, whether
a tool returned it this turn or it was recommended earlier. A blocked card
triggers one corrective retry; if that still breaks a constraint, the blocked
cards are dropped and the reply is replaced by a fixed safe message.

Worst case per turn: 6 model calls for the first answer, 2 for a validation
retry, and 4 more if the safety retry is needed.
"""

import logging
from collections.abc import Iterable, Sequence

from app.agent.answer import FinalAnswer
from app.agent.errors import AgentAnswerError, AgentLoopError
from app.agent.grounding import grounded_items
from app.agent.llm_client import InputItem, LLMClient
from app.agent.schemas import AgentReply, cards_for
from app.agent.tool_rounds import MAX_TOOL_ROUNDS, RETRY_TOOL_ROUNDS, Turn, final_answer
from app.menu.constraints import HardConstraints
from app.safety.guard import Blocked, GuardResult, check
from app.tools.context import ToolContext

logger = logging.getLogger(__name__)

NO_SAFE_MATCH = (
    "I could not find a dish that fits your saved allergies and diet for that. "
    "Could you tell me a bit more about what you feel like?"
)
SAFE_MATCHES = "Here are options that fit your saved allergies and diet."


async def run_turn(
    client: LLMClient,
    context: ToolContext,
    input_items: Sequence[InputItem],
    seen_ids: Iterable[int] = (),
    *,
    instructions: str,
) -> AgentReply:
    """`seen_ids`: items recommended earlier in this conversation, allowed as cards again.
    The context carries the guest's constraints, so no caller can skip enforcement."""
    constraints = context.constraints
    turn = Turn(client, context, instructions, list(input_items), set(seen_ids))
    answer = await final_answer(turn, MAX_TOOL_ROUNDS)
    guard = await _guard(turn, answer)
    if not guard.blocked:
        return AgentReply(reply=answer.reply, items=cards_for(guard.allowed, constraints))
    turn.items.append({"role": "assistant", "content": answer.model_dump_json()})
    turn.items.append({"role": "developer", "content": _blocked_note(guard.blocked)})
    try:
        answer = await final_answer(turn, RETRY_TOOL_ROUNDS)
    except (AgentLoopError, AgentAnswerError):
        # A failed retry must not turn a safe outcome into an error (and roll back
        # an allergy stated in this very message): fall back to the safe reply.
        logger.warning("safety_retry_failed")
        return _fallback(guard, constraints)
    retried = await _guard(turn, answer)
    if retried.blocked:
        return _fallback(retried, constraints)
    return AgentReply(reply=answer.reply, items=cards_for(retried.allowed, constraints))


def _fallback(guard: GuardResult, constraints: HardConstraints) -> AgentReply:
    reply = SAFE_MATCHES if guard.allowed else NO_SAFE_MATCH
    return AgentReply(reply=reply, items=cards_for(guard.allowed, constraints))


async def _guard(turn: Turn, answer: FinalAnswer) -> GuardResult:
    context = turn.context
    items = await grounded_items(
        context.session, context.restaurant_id, answer.recommended_item_ids, turn.seen_ids
    )
    result = check(items, context.constraints)
    for blocked in result.blocked:
        logger.warning(
            "safety_blocked id=%d reasons=%s", blocked.item_id, ",".join(blocked.reasons)
        )
    return result


def _blocked_note(blocked: list[Blocked]) -> str:
    removed = "; ".join(f"{b.name} (id {b.item_id}): {', '.join(b.reasons)}" for b in blocked)
    return (
        "These recommendations were removed because they break the guest's saved "
        f"allergies or diet: {removed}. Do not recommend them. Recommend only items "
        "that fit, or say plainly that nothing fits. Return the corrected JSON answer."
    )
