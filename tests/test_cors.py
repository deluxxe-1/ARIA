import json

import pytest
from fastapi.testclient import TestClient

from app.core.settings import get_settings
from app.main import create_app


def _build_client(monkeypatch: pytest.MonkeyPatch, **env_vars: str) -> TestClient:
    get_settings.cache_clear()
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


def test_cors_origen_autorizado_recibe_header(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(
        monkeypatch,
        ARIA_ENABLE_CORS="true",
        ARIA_CORS_ORIGINS=json.dumps(["http://bueno.com"]),
    )
    with client as c:
        response = c.get("/health", headers={"Origin": "http://bueno.com"})

    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == "http://bueno.com"


def test_cors_origen_no_autorizado_sin_header(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(
        monkeypatch,
        ARIA_ENABLE_CORS="true",
        ARIA_CORS_ORIGINS=json.dumps(["http://bueno.com"]),
    )
    with client as c:
        response = c.get("/health", headers={"Origin": "http://malo.com"})

    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" not in response.headers


def test_cors_desactivado_sin_header_incluso_origen_bueno(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(
        monkeypatch,
        ARIA_ENABLE_CORS="false",
        ARIA_CORS_ORIGINS=json.dumps(["http://bueno.com"]),
    )
    with client as c:
        response = c.get("/health", headers={"Origin": "http://bueno.com"})

    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" not in response.headers
