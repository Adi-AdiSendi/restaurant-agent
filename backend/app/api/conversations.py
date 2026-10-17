"""Start a new conversation for the logged-in user."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user_id
from app.db.engine import get_session
from app.memory.conversations import create_conversation

router = APIRouter()


class NewConversation(BaseModel):
    id: int


@router.post("/conversations", status_code=201)
async def new_conversation(
    user_id: int = Depends(current_user_id), session: AsyncSession = Depends(get_session)
) -> NewConversation:
    conversation_id = await create_conversation(session, user_id)
    await session.commit()
    return NewConversation(id=conversation_id)
