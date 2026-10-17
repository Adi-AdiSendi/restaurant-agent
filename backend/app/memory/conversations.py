"""Conversations and their messages. Ownership is checked against user_id."""

from collections.abc import Sequence
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.models import Conversation, Message

HISTORY_LIMIT = 20


async def create_conversation(session: AsyncSession, user_id: int) -> int:
    conversation = Conversation(user_id=user_id)
    session.add(conversation)
    await session.flush()
    return conversation.id


async def is_owned_by(session: AsyncSession, user_id: int, conversation_id: int) -> bool:
    stmt = select(Conversation.id).where(
        Conversation.id == conversation_id, Conversation.user_id == user_id
    )
    return await session.scalar(stmt) is not None


async def recent_messages(
    session: AsyncSession, user_id: int, conversation_id: int, limit: int = HISTORY_LIMIT
) -> Sequence[Message]:
    """The last `limit` messages, oldest first. Empty if the user does not own it."""
    stmt = (
        select(Message)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(Message.conversation_id == conversation_id, Conversation.user_id == user_id)
        .order_by(Message.id.desc())
        .limit(limit)
    )
    return list(reversed((await session.scalars(stmt)).all()))


async def add_message(
    session: AsyncSession,
    conversation_id: int,
    role: Literal["user", "assistant"],
    content: str,
    recommended_item_ids: Sequence[int] = (),
) -> Message:
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        recommended_item_ids=list(recommended_item_ids),
    )
    session.add(message)
    await session.flush()
    return message
