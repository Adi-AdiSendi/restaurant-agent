from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.frontend import mount_frontend


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    (tmp_path / "index.html").write_text("<html>spa</html>", encoding="utf-8")
    (tmp_path / "app.js").write_text("console.log(1)", encoding="utf-8")
    app = FastAPI()
    mount_frontend(app, tmp_path)
    return TestClient(app)


def test_client_route_falls_back_to_index(client: TestClient) -> None:
    response = client.get("/chat/123")
    assert response.status_code == 200
    assert "spa" in response.text


def test_existing_asset_is_served(client: TestClient) -> None:
    assert client.get("/app.js").text == "console.log(1)"


def test_missing_asset_is_404(client: TestClient) -> None:
    assert client.get("/missing.js").status_code == 404


def test_unknown_api_route_is_json_404(client: TestClient) -> None:
    response = client.get("/api/nope")
    assert response.status_code == 404
    assert response.json() == {"detail": "Unknown API route: /api/nope"}


def test_head_on_unknown_api_route_is_404(client: TestClient) -> None:
    assert client.head("/api/nope").status_code == 404


def test_missing_build_serves_api_only(tmp_path: Path) -> None:
    app = FastAPI()
    mount_frontend(app, tmp_path / "no-dist")
    client = TestClient(app)
    assert client.get("/").status_code == 404
    assert client.get("/api/nope").json() == {"detail": "Unknown API route: /api/nope"}
