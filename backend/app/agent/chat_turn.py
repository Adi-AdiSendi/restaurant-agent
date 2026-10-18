"""One user message, end to end: store it, update memory, reply, store the reply.

Everything runs in one transaction. If any step fails nothing is committed, so
a retry does not duplicate messages or memory. The user's row is locked for the
turn, so a double-submit waits instead of racing on the same preferences.
Trade-off: the transaction stays open across the LLM calls (see README).
A turn that passes its deadline is rolled back the same way.
"""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.context import build_input, memory_update_note
from app.agent.errors import TurnTimeoutError
from app.agent.llm_client import AgentLLM
from app.agent.loop import run_turn
from app.agent.prompt import system_prompt
from app.agent.schemas import AgentReply
from app.memory.conversations import add_message, owned_conversation, recent_messages
from app.memory.extract import extract_operations
from app.memory.profile import dislikes, hard_constraints, load_profile
from app.memory.supersede import apply_operations
from app.menu.queries import get_restaurant, list_restaurants
from app.tools.context import ToolContext
from app.users.service import lock_user


class ConversationNotFoundError(Exception):
    """The conversation does not exist or belongs to another user."""


async def handle_message(
    llm: AgentLLM,
    session: AsyncSession,
    user_id: int,
    conversation_id: int,
    text: str,
    deadline_seconds: float,
) -> AgentReply:
    deadline = asyncio.timeout(deadline_seconds)
    try:
        async with deadline:
            reply = await _turn(llm, session, user_id, conversation_id, text)
    except Exception as exc:
        await session.rollback()
        # Only our deadline is a 504; other timeouts (e.g. a DB connect) are not.
        if isinstance(exc, TimeoutError) and deadline.expired():
            raise TurnTimeoutError from exc
        raise
    await session.commit()
    return reply


async def _turn(
    llm: AgentLLM, session: AsyncSession, user_id: int, conversation_id: int, text: str
) -> AgentReply:
    conversation = await owned_conversation(session, user_id, conversation_id)
    if conversation is None:
        raise ConversationNotFoundError
    restaurant = await get_restaurant(session, conversation.restaurant_id)
    assert restaurant is not None, "conversations.restaurant_id is a foreign key"
    await lock_user(session, user_id)
    history = list(await recent_messages(session, user_id, conversation_id))
    previous = next((m.content for m in reversed(history) if m.role == "assistant"), None)
    user_message = await add_message(session, conversation_id, "user", text)

    before = await load_profile(session, user_id)
    ops = await extract_operations(llm, before, previous, text)
    await apply_operations(session, user_id, ops, user_message.id)

    profile = await load_profile(session, user_id)
    note = memory_update_note(before, profile)
    items, seen = build_input(profile, [*history, user_message], note)
    context = ToolContext(
        session,
        user_id,
        conversation_id,
        restaurant.id,
        restaurant.slug,
        tuple(restaurant.categories),
        hard_constraints(profile),
        dislikes(profile),
    )
    others = [r for r in await list_restaurants(session) if r.id != restaurant.id]
    instructions = system_prompt(restaurant, others)
    reply = await run_turn(llm, context, items, seen, instructions=instructions)

    item_ids = [item.id for item in reply.items]
    await add_message(session, conversation_id, "assistant", reply.reply, item_ids)
    return reply
