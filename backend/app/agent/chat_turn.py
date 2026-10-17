"""One user message, end to end: store it, update memory, reply, store the reply.

Everything runs in one transaction. If any step fails nothing is committed, so
a retry does not duplicate messages or memory. The user's row is locked for the
turn, so a double-submit waits instead of racing on the same preferences.
Trade-off: the transaction stays open across the LLM calls (see README).
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.context import build_input
from app.agent.llm_client import AgentLLM
from app.agent.loop import run_turn
from app.agent.schemas import AgentReply
from app.memory.conversations import add_message, is_owned_by, recent_messages
from app.memory.extract import extract_operations
from app.memory.profile import hard_constraints, load_profile
from app.memory.supersede import apply_operations
from app.users.service import lock_user


class ConversationNotFoundError(Exception):
    """The conversation does not exist or belongs to another user."""


async def handle_message(
    llm: AgentLLM, session: AsyncSession, user_id: int, conversation_id: int, text: str
) -> AgentReply:
    try:
        reply = await _turn(llm, session, user_id, conversation_id, text)
    except Exception:
        await session.rollback()
        raise
    await session.commit()
    return reply


async def _turn(
    llm: AgentLLM, session: AsyncSession, user_id: int, conversation_id: int, text: str
) -> AgentReply:
    if not await is_owned_by(session, user_id, conversation_id):
        raise ConversationNotFoundError
    await lock_user(session, user_id)
    history = list(await recent_messages(session, user_id, conversation_id))
    previous = next((m.content for m in reversed(history) if m.role == "assistant"), None)
    user_message = await add_message(session, conversation_id, "user", text)

    ops = await extract_operations(llm, await load_profile(session, user_id), previous, text)
    await apply_operations(session, user_id, ops, user_message.id)

    profile = await load_profile(session, user_id)
    items, seen = build_input(profile, [*history, user_message])
    reply = await run_turn(llm, session, items, seen, constraints=hard_constraints(profile))

    item_ids = [item.id for item in reply.items]
    await add_message(session, conversation_id, "assistant", reply.reply, item_ids)
    return reply
