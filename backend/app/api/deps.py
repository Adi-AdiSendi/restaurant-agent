"""Shared route dependencies. The session cookie is the only source of user_id."""

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_session
from app.memory.profile import hard_constraints, load_profile, tastes
from app.menu import clock
from app.menu.constraints import HardConstraints
from app.menu.taste import Tastes
from app.orders.orders import kcal_since
from app.users.service import get_username


async def current_user_id(request: Request, session: AsyncSession = Depends(get_session)) -> int:
    user_id = request.session.get("user_id")
    if not isinstance(user_id, int) or await get_username(session, user_id) is None:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Please log in.")
    return user_id


async def guest_constraints(
    user_id: int = Depends(current_user_id), session: AsyncSession = Depends(get_session)
) -> HardConstraints:
    """The logged-in guest's saved allergies and diet, as the server enforces them."""
    return hard_constraints(await load_profile(session, user_id))


async def guest_tastes(
    user_id: int = Depends(current_user_id), session: AsyncSession = Depends(get_session)
) -> Tastes:
    """The guest's soft tastes for today (Riyadh): dislikes, day rules, budget, spice, kcal."""
    today = await kcal_since(session, user_id, clock.start_of_day())
    return tastes(await load_profile(session, user_id), clock.weekday(), today)
