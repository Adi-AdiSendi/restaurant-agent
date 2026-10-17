"""GET /api/restaurants: every restaurant in the app, in display order. Public."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_session
from app.menu.queries import list_restaurants
from app.menu.restaurant_schemas import RestaurantOut

router = APIRouter()


@router.get("/restaurants")
async def restaurants(session: AsyncSession = Depends(get_session)) -> list[RestaurantOut]:
    return [RestaurantOut.model_validate(r) for r in await list_restaurants(session)]
