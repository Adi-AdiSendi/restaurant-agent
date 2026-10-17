"""Shared route dependencies. The session cookie is the only source of user_id."""

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_session
from app.users.service import get_username


async def current_user_id(request: Request, session: AsyncSession = Depends(get_session)) -> int:
    user_id = request.session.get("user_id")
    if not isinstance(user_id, int) or await get_username(session, user_id) is None:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Please log in.")
    return user_id
