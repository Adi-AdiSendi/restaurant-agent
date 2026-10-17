"""What the assistant remembers about the logged-in user, including past facts."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user_id
from app.db.engine import get_session
from app.memory.profile import PreferenceOut, preference_history

router = APIRouter()


@router.get("/preferences")
async def preferences(
    user_id: int = Depends(current_user_id), session: AsyncSession = Depends(get_session)
) -> list[PreferenceOut]:
    return await preference_history(session, user_id)
