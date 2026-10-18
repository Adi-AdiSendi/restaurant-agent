"""Read a user's preferences. Always scoped by user_id."""

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.preference import Preference
from app.memory.vocabulary import Diet, Kind, Status
from app.menu.allergens import Allergen
from app.menu.constraints import HardConstraints
from app.menu.taste import Tastes


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


def dislikes(profile: Sequence[Preference]) -> tuple[str, ...]:
    """Soft dislikes, e.g. "pickles": a cart add leaves them out where the dish allows."""
    return tuple(p.value for p in profile if p.kind == Kind.DISLIKE)


def hard_constraints(profile: Sequence[Preference]) -> HardConstraints:
    """The allergies and diet that `safety/` and `search_menu` enforce in code."""
    allergens = frozenset(Allergen(p.value) for p in profile if p.kind == Kind.ALLERGY)
    diets = {p.value for p in profile if p.kind == Kind.DIET}
    vegan = Diet.VEGAN in diets
    return HardConstraints(
        excluded_allergens=allergens, vegan=vegan, vegetarian=vegan or Diet.VEGETARIAN in diets
    )


_SPICE_LEVEL = {"none": 0, "mild": 1, "medium": 2, "hot": 3}


def tastes(profile: Sequence[Preference], weekday: str, kcal_today: int) -> Tastes:
    """The soft side of the profile, for "Matches my tastes" (never enforced)."""
    values = {kind: [p.value for p in profile if p.kind == kind] for kind in Kind}
    today = [
        rule.split(": ", 1)[1]
        for rule in values[Kind.DAY_DISLIKE]
        if rule.startswith(f"{weekday}:")
    ]
    budget, spice, goal = values[Kind.BUDGET], values[Kind.SPICE], values[Kind.CALORIES]
    return Tastes(
        dislikes=tuple(values[Kind.DISLIKE]),
        likes=tuple(values[Kind.LIKE]),
        today_avoid=tuple(today),
        weekday=weekday,
        budget=Decimal(budget[0]) if budget else None,
        max_spice=_SPICE_LEVEL.get(spice[0]) if spice else None,
        kcal_left=int(goal[0]) - kcal_today if goal else None,
    )
