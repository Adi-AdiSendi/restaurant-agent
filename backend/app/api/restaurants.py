"""Restaurants: the public list, and one menu as the logged-in guest sees it."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import guest_constraints, guest_tastes
from app.db.engine import get_session
from app.menu.constraints import HardConstraints
from app.menu.guest_menu import GuestMenu, guest_menu
from app.menu.queries import list_restaurants
from app.menu.restaurant_schemas import RestaurantOut
from app.menu.taste import Tastes

router = APIRouter()


@router.get("/restaurants")
async def restaurants(session: AsyncSession = Depends(get_session)) -> list[RestaurantOut]:
    return [RestaurantOut.model_validate(r) for r in await list_restaurants(session)]


@router.get("/restaurants/{slug}/menu")
async def menu(
    slug: str,
    constraints: HardConstraints = Depends(guest_constraints),
    tastes: Tastes = Depends(guest_tastes),
    session: AsyncSession = Depends(get_session),
) -> GuestMenu:
    """Login required: every dish carries what conflicts with this guest's profile."""
    found = await guest_menu(session, slug, constraints, tastes)
    if found is None:
        raise HTTPException(status_code=404, detail=f"No restaurant {slug!r}.")
    return found
