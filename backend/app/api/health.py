"""Liveness check used by the host, the keep-awake ping and the UI. It never touches the DB."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class Health(BaseModel):
    status: str


@router.get("/health")
async def health() -> Health:
    return Health(status="ok")
