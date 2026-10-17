"""Serve the built React app, falling back to index.html for client routes."""

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

logger = logging.getLogger(__name__)


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Response:
        is_client_route = "." not in Path(path).name
        try:
            response = await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404 and is_client_route:
                return await super().get_response("index.html", scope)
            raise
        if response.status_code == 404 and is_client_route:
            return await super().get_response("index.html", scope)
        return response


async def unknown_api_route(rest: str) -> None:
    raise HTTPException(status_code=404, detail=f"Unknown API route: /api/{rest}")


def mount_frontend(app: FastAPI, dist: Path) -> None:
    """Unknown /api paths return JSON 404s; everything else is the SPA.

    Call this after every API router: the /api catch-all hides routes added later.
    """
    app.add_api_route(
        "/api/{rest:path}",
        unknown_api_route,
        methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"],
        include_in_schema=False,
    )
    if not (dist / "index.html").is_file():
        logger.warning("frontend_build_missing dist=%s; serving the API only", dist)
        return
    app.mount("/", SPAStaticFiles(directory=dist, html=True), name="frontend")
