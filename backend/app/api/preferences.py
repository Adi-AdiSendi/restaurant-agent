"""What the assistant remembers about the logged-in user, including past facts.

Edits are in `preference_edits.py`."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user_id
from app.db.engine import get_session
from app.memory.profile import PreferenceOut, preference_history
from app.memory.vocabulary import CALORIES_MAX, CALORIES_MIN, WEEKDAYS, Diet, Spice
from app.menu import clock
from app.menu.allergens import Allergen
from app.orders.orders import kcal_since

router = APIRouter()


class Today(BaseModel):
    weekday: str
    """Today in Riyadh, lowercase: day rules for this day apply."""
    kcal: int
    """Estimated kcal of the guest's orders placed today (Riyadh time)."""


class Vocabulary(BaseModel):
    """The values each kind accepts, so the Preferences page never keeps its own copy."""

    allergens: list[Allergen]
    diets: list[Diet]
    spice_levels: list[Spice]
    weekdays: list[str]
    calories_min: int = CALORIES_MIN
    calories_max: int = CALORIES_MAX


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


@router.get("/preferences/vocabulary")
async def vocabulary() -> Vocabulary:
    return Vocabulary(
        allergens=list(Allergen),
        diets=list(Diet),
        spice_levels=list(Spice),
        weekdays=list(WEEKDAYS),
    )
