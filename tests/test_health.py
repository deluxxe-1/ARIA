from app.main import create_app
from fastapi.testclient import TestClient


def test_health_endpoint_returns_ok() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "planner_model" in data
    assert "coder_model" in data
