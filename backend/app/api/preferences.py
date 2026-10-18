"""What the assistant remembers about the logged-in user, including past facts."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user_id
from app.db.engine import get_session
from app.memory.profile import PreferenceOut, preference_history
from app.menu import clock
from app.orders.orders import kcal_since

router = APIRouter()


class Today(BaseModel):
    weekday: str
    """Today in Riyadh, lowercase: day rules for this day apply."""
    kcal: int
    """Estimated kcal of the guest's orders placed today (Riyadh time)."""


@router.get("/preferences")
async def preferences(
    user_id: int = Depends(current_user_id), session: AsyncSession = Depends(get_session)
) -> list[PreferenceOut]:
    return await preference_history(session, user_id)


@router.get("/preferences/today")
async def today(
    user_id: int = Depends(current_user_id), session: AsyncSession = Depends(get_session)
) -> Today:
    kcal = await kcal_since(session, user_id, clock.start_of_day())
    return Today(weekday=clock.weekday(), kcal=kcal)
