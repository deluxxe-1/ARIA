import pytest
from fastapi.testclient import TestClient

from app.core.settings import get_settings
from app.main import create_app


def _build_client(monkeypatch: pytest.MonkeyPatch, **env_vars: str) -> TestClient:
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


def test_api_key_desactivada_peticiones_pasan(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(
        monkeypatch,
        ARIA_ENABLE_API_KEY="false",
        ARIA_API_KEY="secret123",
    )
    with client as c:
        health_resp = c.get("/health")
        chat_resp = c.post("/chat", json={})

    assert health_resp.status_code == 200
    assert chat_resp.status_code != 401
    assert chat_resp.status_code == 422


def test_api_key_activada_sin_header_retorna_401(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(
        monkeypatch,
        ARIA_ENABLE_API_KEY="true",
        ARIA_API_KEY="secret123",
    )
    with client as c:
        response = c.post("/chat", json={})

    assert response.status_code == 401
    assert response.json() == {"detail": "API key invalida."}


def test_api_key_activada_con_header_correcto_pasa(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(
        monkeypatch,
        ARIA_ENABLE_API_KEY="true",
        ARIA_API_KEY="secret123",
    )
    with client as c:
        response = c.post("/chat", json={}, headers={"X-ARIA-Key": "secret123"})

    assert response.status_code != 401
    assert response.status_code == 422


def test_api_key_activada_health_no_requiere_key(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(
        monkeypatch,
        ARIA_ENABLE_API_KEY="true",
        ARIA_API_KEY="secret123",
    )
    with client as c:
        response = c.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
