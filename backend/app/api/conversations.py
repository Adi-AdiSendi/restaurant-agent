"""Start a new conversation for the logged-in user, at one restaurant."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user_id
from app.db.engine import get_session
from app.memory.conversations import start_conversation

router = APIRouter()


class NewConversationRequest(BaseModel):
    restaurant: str = Field(default="corner-table", max_length=40)


class NewConversation(BaseModel):
    id: int


@router.post("/conversations", status_code=201)
async def new_conversation(
    body: NewConversationRequest | None = None,
    user_id: int = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> NewConversation:
    slug = (body or NewConversationRequest()).restaurant
    conversation_id = await start_conversation(session, user_id, slug)
    if conversation_id is None:
        raise HTTPException(status_code=404, detail=f"No restaurant {slug!r}.")
    await session.commit()
    return NewConversation(id=conversation_id)
