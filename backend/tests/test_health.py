from fastapi.testclient import TestClient

from transport_erp.main import create_app


def test_liveness_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
