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


def _create_duty(client: TestClient, *, duty_number: str = "Н-001") -> str:
    stop_a = client.post(
        "/api/stops", json={"name": f"А-{duty_number}", "locality": "Львів", "active": True}
    )
    stop_b = client.post(
        "/api/stops", json={"name": f"Б-{duty_number}", "locality": "Львів", "active": True}
    )
    route = client.post(
        "/api/routes",
        json={
            "number": duty_number,
            "name": f"Маршрут {duty_number}",
            "active": True,
            "stop_ids": [stop_a.json()["id"], stop_b.json()["id"]],
        },
    )
    schedule = client.post(
        "/api/schedules",
        json={
            "route_id": route.json()["id"],
            "departure_time": "08:00" if duty_number == "Н-001" else "10:00",
            "arrival_time": "09:00" if duty_number == "Н-001" else "11:00",
            "active": True,
        },
    )
    assert schedule.status_code == 201

    suffix = "101" if duty_number == "Н-001" else "102"
    vehicle = client.post(
        "/api/vehicles",
        json={
            "fleet_number": suffix,
            "registration_number": f"BC0{suffix}AA",
            "vin": f"VIN-{suffix}",
            "make": "Ataman",
            "model": "A092",
            "year": 2020,
            "lifecycle_status": "ACTIVE",
        },
    )
    driver = client.post(
        "/api/drivers",
        json={
            "personnel_number": f"D-{suffix}",
            "last_name": f"Водій{suffix}",
            "first_name": "Тест",
            "middle_name": None,
            "phone": None,
            "employment_status": "ACTIVE",
        },
    )
    generated = client.post("/api/trips/generate", json={"service_date": "2026-09-20"})
    assert generated.status_code == 200
    trip = next(item for item in generated.json() if item["route_id"] == route.json()["id"])
    duty = client.post(
        "/api/duties",
        json={
            "service_date": "2026-09-20",
            "duty_number": duty_number,
            "vehicle_id": vehicle.json()["id"],
            "driver_id": driver.json()["id"],
            "trip_ids": [trip["id"]],
        },
    )
    assert duty.status_code == 201
    return str(duty.json()["id"])


def _release(client: TestClient, duty_id: str) -> None:
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


def test_waybill_requires_released_duty(client: TestClient) -> None:
    duty_id = _create_duty(client)
    blocked = client.post("/api/waybills", json={"duty_id": duty_id, "number": "ШЛ-001"})
    assert blocked.status_code == 409
    assert "випущеного" in blocked.json()["detail"]


def test_released_duty_becomes_candidate_and_waybill_is_created(client: TestClient) -> None:
    duty_id = _create_duty(client)
    _release(client, duty_id)

    candidates = client.get("/api/waybill-candidates", params={"service_date": "2026-09-20"})
    assert candidates.status_code == 200
    assert len(candidates.json()) == 1
    assert candidates.json()[0]["duty_id"] == duty_id

    created = client.post("/api/waybills", json={"duty_id": duty_id, "number": "ШЛ-001"})
    assert created.status_code == 201
    body = created.json()
    assert body["number"] == "ШЛ-001"
    assert body["status"] == "OPEN"
    assert body["duty_number"] == "Н-001"
    assert body["medical_checked_by"] == "Медик"
    assert body["technical_checked_by"] == "Механік"
    assert body["dispatcher_checked_by"] == "Диспетчер"
    assert len(body["trips"]) == 1

    after = client.get("/api/waybill-candidates", params={"service_date": "2026-09-20"})
    assert after.status_code == 200
    assert after.json() == []


def test_waybill_number_and_duty_are_unique(client: TestClient) -> None:
    first_duty = _create_duty(client, duty_number="Н-001")
    second_duty = _create_duty(client, duty_number="Н-002")
    _release(client, first_duty)
    _release(client, second_duty)

    first = client.post("/api/waybills", json={"duty_id": first_duty, "number": "ШЛ-001"})
    assert first.status_code == 201

    duplicate_duty = client.post(
        "/api/waybills", json={"duty_id": first_duty, "number": "ШЛ-002"}
    )
    assert duplicate_duty.status_code == 409

    duplicate_number = client.post(
        "/api/waybills", json={"duty_id": second_duty, "number": "ШЛ-001"}
    )
    assert duplicate_number.status_code == 409


def test_waybill_can_be_loaded_by_id(client: TestClient) -> None:
    duty_id = _create_duty(client)
    _release(client, duty_id)
    created = client.post("/api/waybills", json={"duty_id": duty_id, "number": "ШЛ-001"})
    assert created.status_code == 201

    loaded = client.get(f"/api/waybills/{created.json()['id']}")
    assert loaded.status_code == 200
    assert loaded.json()["number"] == "ШЛ-001"


def test_waybill_taxo_pdf_is_generated_in_persistent_documents(
    client: TestClient, tmp_path: Path
) -> None:
    duty_id = _create_duty(client)
    _release(client, duty_id)
    created = client.post("/api/waybills", json={"duty_id": duty_id, "number": "ШЛ-001"})
    assert created.status_code == 201

    response = client.get(f"/api/waybills/{created.json()['id']}/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF")

    expected = tmp_path / "data" / "documents" / "waybills" / "2026" / "09" / "Waybill_ШЛ-001.pdf"
    assert expected.is_file()
    assert expected.read_bytes().startswith(b"%PDF")
