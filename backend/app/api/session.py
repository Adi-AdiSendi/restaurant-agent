"""Signed session cookie. It holds only the user ID (ADR 0013)."""

import logging
import secrets

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.config import Settings

COOKIE_NAME = "ra_session"
MAX_AGE_SECONDS = 30 * 24 * 3600
logger = logging.getLogger(__name__)


def add_session_middleware(app: FastAPI, settings: Settings) -> None:
    secret = settings.session_secret
    if not secret:
        # Only reachable outside production (see Settings); sessions reset on restart.
        logger.warning("session_secret_missing using a random per-process secret")
        secret = secrets.token_urlsafe(32)
    app.add_middleware(
        SessionMiddleware,
        secret_key=secret,
        session_cookie=COOKIE_NAME,
        max_age=MAX_AGE_SECONDS,
        same_site="lax",
        https_only=settings.app_env == "production",
    )
