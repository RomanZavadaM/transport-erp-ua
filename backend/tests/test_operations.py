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


def _route(client: TestClient) -> str:
    first = client.post("/api/stops", json={"name": "А", "locality": "Львів", "active": True})
    second = client.post("/api/stops", json={"name": "Б", "locality": "Львів", "active": True})
    assert first.status_code == second.status_code == 201
    route = client.post(
        "/api/routes",
        json={
            "number": "1",
            "name": "А — Б",
            "active": True,
            "stop_ids": [first.json()["id"], second.json()["id"]],
        },
    )
    assert route.status_code == 201
    return str(route.json()["id"])


def _vehicle(client: TestClient, number: str) -> str:
    response = client.post(
        "/api/vehicles",
        json={
            "fleet_number": number,
            "registration_number": f"BC{number.zfill(4)}AA",
            "vin": f"VIN-{number}",
            "make": "Ataman",
            "model": "A092",
            "year": 2020,
            "lifecycle_status": "ACTIVE",
        },
    )
    assert response.status_code == 201
    return str(response.json()["id"])


def _driver(client: TestClient, number: str) -> str:
    response = client.post(
        "/api/drivers",
        json={
            "personnel_number": number,
            "last_name": f"Водій{number}",
            "first_name": "Тест",
            "middle_name": None,
            "phone": None,
            "employment_status": "ACTIVE",
        },
    )
    assert response.status_code == 201
    return str(response.json()["id"])


def _schedule(client: TestClient, route_id: str, departure: str, arrival: str) -> str:
    response = client.post(
        "/api/schedules",
        json={
            "route_id": route_id,
            "departure_time": departure,
            "arrival_time": arrival,
            "active": True,
        },
    )
    assert response.status_code == 201
    return str(response.json()["id"])


def test_generate_trips_and_create_multi_trip_duty(client: TestClient) -> None:
    route_id = _route(client)
    _schedule(client, route_id, "08:00", "09:00")
    _schedule(client, route_id, "09:20", "10:20")
    vehicle_id = _vehicle(client, "101")
    driver_id = _driver(client, "D-001")

    generated = client.post("/api/trips/generate", json={"service_date": "2026-09-17"})
    assert generated.status_code == 200
    trips = generated.json()
    assert [trip["planned_departure"] for trip in trips] == ["08:00", "09:20"]

    duty = client.post(
        "/api/duties",
        json={
            "service_date": "2026-09-17",
            "duty_number": "Н-001",
            "vehicle_id": vehicle_id,
            "driver_id": driver_id,
            "trip_ids": [trip["id"] for trip in trips],
        },
    )
    assert duty.status_code == 201
    assert duty.json()["duty_number"] == "Н-001"
    assert len(duty.json()["trips"]) == 2

    listed = client.get("/api/trips", params={"service_date": "2026-09-17"})
    assert listed.status_code == 200
    assert all(trip["status"] == "ASSIGNED" for trip in listed.json())
    assert all(trip["duty_number"] == "Н-001" for trip in listed.json())


def test_vehicle_and_driver_cannot_overlap(client: TestClient) -> None:
    route_id = _route(client)
    _schedule(client, route_id, "08:00", "09:00")
    _schedule(client, route_id, "08:30", "09:30")
    vehicle_1 = _vehicle(client, "101")
    vehicle_2 = _vehicle(client, "102")
    driver_1 = _driver(client, "D-001")
    driver_2 = _driver(client, "D-002")

    generated = client.post("/api/trips/generate", json={"service_date": "2026-09-18"})
    assert generated.status_code == 200
    first_trip, second_trip = generated.json()

    first_duty = client.post(
        "/api/duties",
        json={
            "service_date": "2026-09-18",
            "duty_number": "Н-001",
            "vehicle_id": vehicle_1,
            "driver_id": driver_1,
            "trip_ids": [first_trip["id"]],
        },
    )
    assert first_duty.status_code == 201

    same_vehicle = client.post(
        "/api/duties",
        json={
            "service_date": "2026-09-18",
            "duty_number": "Н-002",
            "vehicle_id": vehicle_1,
            "driver_id": driver_2,
            "trip_ids": [second_trip["id"]],
        },
    )
    assert same_vehicle.status_code == 409
    assert "Автобус" in same_vehicle.json()["detail"]

    same_driver = client.post(
        "/api/duties",
        json={
            "service_date": "2026-09-18",
            "duty_number": "Н-003",
            "vehicle_id": vehicle_2,
            "driver_id": driver_1,
            "trip_ids": [second_trip["id"]],
        },
    )
    assert same_driver.status_code == 409
    assert "Водій" in same_driver.json()["detail"]
