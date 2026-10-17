"""Read a user's preferences. Always scoped by user_id."""

from collections.abc import Sequence
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.preference import Preference
from app.memory.vocabulary import Diet, Kind, Status
from app.menu.allergens import Allergen
from app.menu.constraints import HardConstraints


class PreferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: Kind
    value: str
    status: Status
    is_hard: bool
    superseded_by: int | None
    created_at: datetime


async def load_profile(session: AsyncSession, user_id: int) -> Sequence[Preference]:
    """Active preferences only: what the agent should act on now."""
    stmt = (
        select(Preference)
        .where(Preference.user_id == user_id, Preference.status == Status.ACTIVE)
        .order_by(Preference.kind, Preference.id)
    )
    return (await session.scalars(stmt)).all()


async def preference_history(session: AsyncSession, user_id: int) -> list[PreferenceOut]:
    """Every row, newest first, including superseded and removed ones."""
    stmt = select(Preference).where(Preference.user_id == user_id).order_by(Preference.id.desc())
    return [PreferenceOut.model_validate(row) for row in await session.scalars(stmt)]


def hard_constraints(profile: Sequence[Preference]) -> HardConstraints:
    """The allergies and diet that `safety/` and `search_menu` enforce in code."""
    allergens = frozenset(Allergen(p.value) for p in profile if p.kind == Kind.ALLERGY)
    diets = {p.value for p in profile if p.kind == Kind.DIET}
    vegan = Diet.VEGAN in diets
    return HardConstraints(
        excluded_allergens=allergens, vegan=vegan, vegetarian=vegan or Diet.VEGETARIAN in diets
    )
