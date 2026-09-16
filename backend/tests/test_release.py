from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from transport_erp.config import get_settings
from transport_erp.infrastructure.database import get_engine, get_session_factory
from transport_erp.main import create_app


def _clear_runtime_caches() -> None:
    get_session_factory.cache_clear()
    get_engine.cache_clear()
    get_settings.cache_clear()


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("TRANSPORT_ERP_DEPLOYMENT_PROFILE", "local")
    monkeypatch.setenv("TRANSPORT_ERP_ENVIRONMENT", "test")
    monkeypatch.setenv("TRANSPORT_ERP_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("TRANSPORT_ERP_DATABASE_URL", raising=False)
    monkeypatch.delenv("TRANSPORT_ERP_FRONTEND_DIR", raising=False)
    _clear_runtime_caches()
    test_client = TestClient(create_app())
    yield test_client
    test_client.close()
    _clear_runtime_caches()


def _create_duty(client: TestClient) -> str:
    stop_a = client.post(
        "/api/stops", json={"name": "А", "locality": "Львів", "active": True}
    )
    stop_b = client.post(
        "/api/stops", json={"name": "Б", "locality": "Львів", "active": True}
    )
    route = client.post(
        "/api/routes",
        json={
            "number": "1",
            "name": "А — Б",
            "active": True,
            "stop_ids": [stop_a.json()["id"], stop_b.json()["id"]],
        },
    )
    schedule = client.post(
        "/api/schedules",
        json={
            "route_id": route.json()["id"],
            "departure_time": "08:00",
            "arrival_time": "09:00",
            "active": True,
        },
    )
    assert schedule.status_code == 201
    vehicle = client.post(
        "/api/vehicles",
        json={
            "fleet_number": "101",
            "registration_number": "BC0101AA",
            "vin": "VIN-101",
            "make": "Ataman",
            "model": "A092",
            "year": 2020,
            "lifecycle_status": "ACTIVE",
        },
    )
    driver = client.post(
        "/api/drivers",
        json={
            "personnel_number": "D-001",
            "last_name": "Іваненко",
            "first_name": "Іван",
            "middle_name": "Іванович",
            "phone": None,
            "employment_status": "ACTIVE",
        },
    )
    generated = client.post("/api/trips/generate", json={"service_date": "2026-09-19"})
    assert generated.status_code == 200
    duty = client.post(
        "/api/duties",
        json={
            "service_date": "2026-09-19",
            "duty_number": "Н-001",
            "vehicle_id": vehicle.json()["id"],
            "driver_id": driver.json()["id"],
            "trip_ids": [generated.json()[0]["id"]],
        },
    )
    assert duty.status_code == 201
    return str(duty.json()["id"])


def test_release_requires_all_three_positive_controls(client: TestClient) -> None:
    duty_id = _create_duty(client)

    early = client.post(f"/api/release-controls/{duty_id}/release")
    assert early.status_code == 409
    assert "медичного" in early.json()["detail"]

    medical = client.post(
        f"/api/release-controls/{duty_id}/medical",
        json={"result": "PASSED", "checked_by": "Медик", "note": None},
    )
    assert medical.status_code == 200

    no_technical = client.post(f"/api/release-controls/{duty_id}/release")
    assert no_technical.status_code == 409
    assert "технічного" in no_technical.json()["detail"]

    technical = client.post(
        f"/api/release-controls/{duty_id}/technical",
        json={"result": "PASSED", "checked_by": "Механік", "note": None},
    )
    assert technical.status_code == 200

    no_dispatcher = client.post(f"/api/release-controls/{duty_id}/release")
    assert no_dispatcher.status_code == 409
    assert "диспетчера" in no_dispatcher.json()["detail"]

    dispatcher = client.post(
        f"/api/release-controls/{duty_id}/dispatcher",
        json={"result": "APPROVED", "checked_by": "Диспетчер", "note": None},
    )
    assert dispatcher.status_code == 200
    assert dispatcher.json()["ready_to_release"] is True

    released = client.post(f"/api/release-controls/{duty_id}/release")
    assert released.status_code == 200
    assert released.json()["released_at"] is not None
    assert released.json()["ready_to_release"] is False


def test_failed_control_blocks_release_and_released_duty_is_locked(client: TestClient) -> None:
    duty_id = _create_duty(client)

    failed = client.post(
        f"/api/release-controls/{duty_id}/medical",
        json={"result": "FAILED", "checked_by": "Медик", "note": "Не допущено"},
    )
    assert failed.status_code == 200
    blocked = client.post(f"/api/release-controls/{duty_id}/release")
    assert blocked.status_code == 409

    assert client.post(
        f"/api/release-controls/{duty_id}/medical",
        json={"result": "PASSED", "checked_by": "Медик", "note": None},
    ).status_code == 200
    assert client.post(
        f"/api/release-controls/{duty_id}/technical",
        json={"result": "PASSED", "checked_by": "Механік", "note": None},
    ).status_code == 200
    assert client.post(
        f"/api/release-controls/{duty_id}/dispatcher",
        json={"result": "APPROVED", "checked_by": "Диспетчер", "note": None},
    ).status_code == 200
    assert client.post(f"/api/release-controls/{duty_id}/release").status_code == 200

    locked = client.post(
        f"/api/release-controls/{duty_id}/technical",
        json={"result": "FAILED", "checked_by": "Механік", "note": "Після випуску"},
    )
    assert locked.status_code == 409
    assert "випущено" in locked.json()["detail"]


def test_release_list_shows_duty_for_selected_date(client: TestClient) -> None:
    duty_id = _create_duty(client)
    response = client.get("/api/release-controls", params={"service_date": "2026-09-19"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["duty_id"] == duty_id
    assert response.json()[0]["medical_result"] == "PENDING"
