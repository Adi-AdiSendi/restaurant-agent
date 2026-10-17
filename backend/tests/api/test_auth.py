import httpx2
import pytest

from app.api.session import COOKIE_NAME
from tests.api.conftest import login


async def test_login_registers_then_recognizes_the_user(client: httpx2.AsyncClient) -> None:
    first = await client.post("/api/auth/login", json={"username": "Sara", "pin": "1234"})
    assert first.json() == {"username": "sara", "is_new": True}
    assert COOKIE_NAME in first.cookies
    again = await client.post("/api/auth/login", json={"username": "sara", "pin": "1234"})
    assert again.json() == {"username": "sara", "is_new": False}


async def test_me_and_logout(client: httpx2.AsyncClient) -> None:
    await login(client, "omar")
    assert (await client.get("/api/auth/me")).json() == {"username": "omar"}
    assert (await client.post("/api/auth/logout")).status_code == 204
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_wrong_pin_is_401_and_sets_no_session(client: httpx2.AsyncClient) -> None:
    await login(client, "lina", "1111")
    await client.post("/api/auth/logout")
    response = await client.post("/api/auth/login", json={"username": "lina", "pin": "2222"})
    assert response.status_code == 401
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_bad_credentials_shape_is_422(client: httpx2.AsyncClient) -> None:
    response = await client.post("/api/auth/login", json={"username": "x", "pin": "12"})
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/auth/me"),
        ("POST", "/api/conversations"),
        ("GET", "/api/preferences"),
        ("POST", "/api/chat"),
    ],
)
async def test_memory_routes_need_a_session(
    client: httpx2.AsyncClient, method: str, path: str
) -> None:
    body = {"conversation_id": 1, "message": "hi"} if path == "/api/chat" else None
    response = await client.request(method, path, json=body)
    assert response.status_code == 401


async def test_forged_cookie_is_rejected(client: httpx2.AsyncClient) -> None:
    client.cookies.set(COOKIE_NAME, "eyJ1c2VyX2lkIjogMX0=.forged.signature")
    assert (await client.get("/api/auth/me")).status_code == 401
