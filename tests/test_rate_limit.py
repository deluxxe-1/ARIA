import re
import pytest
from fastapi.testclient import TestClient

from app.core.settings import get_settings
from app.main import create_app

_UUID_HEX_RE = re.compile(r"^[0-9a-f]{32}$")


def _build_client(monkeypatch: pytest.MonkeyPatch, **env_vars: str) -> TestClient:
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


def test_rate_limit_2_peticiones_ok_tercera_429(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(
        monkeypatch,
        ARIA_ENABLE_RATE_LIMIT="true",
        ARIA_RATE_LIMIT_PER_MINUTE="2",
    )
    with client as c:
        r1 = c.get("/health")
        r2 = c.get("/health")
        r3 = c.get("/health")

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 429
    assert r3.headers.get("Retry-After") == "60"
    assert r3.json() == {"detail": "Demasiadas peticiones en poco tiempo."}


def test_rate_limit_desactivado_100_peticiones_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(
        monkeypatch,
        ARIA_ENABLE_RATE_LIMIT="false",
        ARIA_RATE_LIMIT_PER_MINUTE="1",
    )
    with client as c:
        responses = [c.get("/health") for _ in range(100)]

    statuses = {r.status_code for r in responses}
    assert statuses == {200}


def test_toda_respuesta_contiene_x_request_id(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(
        monkeypatch,
        ARIA_ENABLE_RATE_LIMIT="true",
        ARIA_RATE_LIMIT_PER_MINUTE="2",
    )
    with client as c:
        ok1 = c.get("/health")
        ok2 = c.get("/health")
        too_many = c.get("/health")

    assert "X-Request-ID" in ok1.headers
    assert _UUID_HEX_RE.match(ok1.headers["X-Request-ID"]) is not None

    assert "X-Request-ID" in ok2.headers
    assert _UUID_HEX_RE.match(ok2.headers["X-Request-ID"]) is not None

    assert "X-Request-ID" in too_many.headers
    assert _UUID_HEX_RE.match(too_many.headers["X-Request-ID"]) is not None
