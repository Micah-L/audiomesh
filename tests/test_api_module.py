from fastapi.testclient import TestClient  # type: ignore[import-not-found]

from audiomesh.api import app


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
