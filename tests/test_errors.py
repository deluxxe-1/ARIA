from pathlib import Path

import pytest
from app.core.errors import (
    ProfileNotFoundError,
    ToolNotSupportedError,
    VoiceBackendError,
    WorkspaceBoundaryError,
)
from app.main import create_app
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def app_with_error_endpoints() -> FastAPI:
    app = create_app()
    test_router = APIRouter()

    @test_router.get("/_error/workspace")
    async def _raise_workspace() -> None:
        raise WorkspaceBoundaryError("La ruta solicitada esta fuera del workspace permitido.")

    @test_router.get("/_error/profile")
    async def _raise_profile() -> None:
        raise ProfileNotFoundError("No existe el perfil de voz 'inexistente'.")

    @test_router.get("/_error/tool")
    async def _raise_tool() -> None:
        raise ToolNotSupportedError("Herramienta no soportada.")

    @test_router.get("/_error/voice")
    async def _raise_voice() -> None:
        raise VoiceBackendError("Backend STT no soportado: no-existo.")

    @test_router.get("/_error/generic")
    async def _raise_generic() -> None:
        # Simular excepcion que revelaria path absoluto si no se captura.
        raise RuntimeError(f"Unexpected state in {Path.home()}/tmp")

    app.include_router(test_router)
    return app


def test_workspace_boundary_maps_to_403(app_with_error_endpoints: FastAPI) -> None:
    with TestClient(app_with_error_endpoints, raise_server_exceptions=False) as client:
        response = client.get("/_error/workspace")
    assert response.status_code == 403
    body = response.json()
    assert body["detail"] == "La ruta solicitada esta fuera del workspace permitido."


def test_profile_not_found_maps_to_404(app_with_error_endpoints: FastAPI) -> None:
    with TestClient(app_with_error_endpoints, raise_server_exceptions=False) as client:
        response = client.get("/_error/profile")
    assert response.status_code == 404
    body = response.json()
    assert "No existe el perfil de voz" in body["detail"]


def test_tool_not_supported_maps_to_400(app_with_error_endpoints: FastAPI) -> None:
    with TestClient(app_with_error_endpoints, raise_server_exceptions=False) as client:
        response = client.get("/_error/tool")
    assert response.status_code == 400
    body = response.json()
    assert "Herramienta no soportada" in body["detail"]


def test_voice_backend_error_maps_to_503_without_leak(app_with_error_endpoints: FastAPI) -> None:
    with TestClient(app_with_error_endpoints, raise_server_exceptions=False) as client:
        response = client.get("/_error/voice")
    assert response.status_code == 503
    body = response.json()
    assert "disponible" in body["detail"] or "Backend de voz" in body["detail"]
    assert "no-existo" not in body["detail"]


def test_unhandled_exception_maps_to_500_without_leak(
    app_with_error_endpoints: FastAPI,
) -> None:
    with TestClient(app_with_error_endpoints, raise_server_exceptions=False) as client:
        response = client.get("/_error/generic")
    assert response.status_code == 500
    body = response.json()
    assert "error interno" in body["detail"].lower() or "procesando" in body["detail"].lower()
    assert str(Path.home()) not in body.get("detail", "")
