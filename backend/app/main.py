"""Create the FastAPI app, mount the API routes and the frontend build."""

import logging

from fastapi import FastAPI

from app.api import (
    auth,
    cart,
    chat,
    conversations,
    health,
    orders,
    preference_edits,
    preferences,
    restaurants,
    transcribe,
)
from app.api.frontend import mount_frontend
from app.api.session import add_session_middleware
from app.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Restaurant Ordering Assistant", version="0.1.0")
    add_session_middleware(app, settings)
    routers = (
        health,
        auth,
        restaurants,
        conversations,
        chat,
        preferences,
        preference_edits,
        cart,
        orders,
        transcribe,
    )
    for module in routers:
        app.include_router(module.router, prefix="/api")
    mount_frontend(app, settings.frontend_dist)
    return app


app = create_app()
