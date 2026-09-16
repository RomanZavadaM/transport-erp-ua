from __future__ import annotations

import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.test_waybills import _create_duty, _release
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


def _create_released_waybill(client: TestClient) -> tuple[str, str]:
    duty_id = _create_duty(client)
    _release(client, duty_id)
    created = client.post(
        "/api/waybills",
        json={"duty_id": duty_id, "number": "ШЛ-500"},
    )
    assert created.status_code == 201
    return str(created.json()["id"]), duty_id


def test_waybill_cannot_close_without_required_actuals(client: TestClient) -> None:
    waybill_id, _ = _create_released_waybill(client)

    response = client.post(f"/api/waybills/{waybill_id}/close")

    assert response.status_code == 409
    assert "фактичний виїзд" in response.json()["detail"]


def test_waybill_actuals_are_saved_and_calculated(client: TestClient) -> None:
    waybill_id, _ = _create_released_waybill(client)

    saved = client.put(
        f"/api/waybills/{waybill_id}/actuals",
        json={
            "actual_departure": "2026-09-20T08:03:00",
            "actual_return": "2026-09-20T09:08:00",
            "odometer_start": 125000,
            "odometer_end": 125042,
            "fuel_start_liters": 40,
            "fuel_issued_liters": 10,
            "fuel_end_liters": 35,
            "note": "Без зауважень",
        },
    )

    assert saved.status_code == 200
    body = saved.json()
    assert body["distance_km"] == 42
    assert body["fuel_consumed_liters"] == 15.0
    assert body["status"] == "OPEN"

    loaded = client.get(f"/api/waybills/{waybill_id}/actuals")
    assert loaded.status_code == 200
    assert loaded.json()["odometer_end"] == 125042


def test_close_waybill_updates_trip_duty_odometer_and_fuel_history(client: TestClient) -> None:
    waybill_id, duty_id = _create_released_waybill(client)
    saved = client.put(
        f"/api/waybills/{waybill_id}/actuals",
        json={
            "actual_departure": "2026-09-20T08:03:00",
            "actual_return": "2026-09-20T09:08:00",
            "odometer_start": 125000,
            "odometer_end": 125042,
            "fuel_start_liters": 40,
            "fuel_issued_liters": 10,
            "fuel_end_liters": 35,
            "note": None,
        },
    )
    assert saved.status_code == 200

    closed = client.post(f"/api/waybills/{waybill_id}/close")

    assert closed.status_code == 200
    assert closed.json()["status"] == "CLOSED"
    assert closed.json()["closed_at"] is not None

    loaded_waybill = client.get(f"/api/waybills/{waybill_id}")
    assert loaded_waybill.status_code == 200
    assert loaded_waybill.json()["status"] == "CLOSED"

    settings = get_settings()
    with sqlite3.connect(settings.local_database_path) as connection:
        connection.row_factory = sqlite3.Row
        duty = connection.execute(
            "SELECT status, vehicle_id FROM duties WHERE id = ?",
            (duty_id,),
        ).fetchone()
        assert duty is not None
        assert duty["status"] == "COMPLETED"
        vehicle_id = str(duty["vehicle_id"])

        trip_statuses = connection.execute(
            """
            SELECT t.status
            FROM trips t
            JOIN duty_trips dt ON dt.trip_id = t.id
            WHERE dt.duty_id = ?
            """,
            (duty_id,),
        ).fetchall()
        assert trip_statuses
        assert {row["status"] for row in trip_statuses} == {"COMPLETED"}

        odometer = connection.execute(
            """
            SELECT reading_km, note
            FROM odometer_readings
            ORDER BY recorded_at
            """
        ).fetchall()
        assert [row["reading_km"] for row in odometer] == [125000, 125042]
        assert "виїзд" in str(odometer[0]["note"])
        assert "повернення" in str(odometer[1]["note"])

    fuel_history = client.get(f"/api/vehicles/{vehicle_id}/fuel-history")
    assert fuel_history.status_code == 200
    rows = fuel_history.json()
    assert len(rows) == 1
    assert rows[0]["waybill_id"] == waybill_id
    assert rows[0]["waybill_number"] == "ШЛ-500"
    assert rows[0]["fuel_start_liters"] == 40.0
    assert rows[0]["fuel_issued_liters"] == 10.0
    assert rows[0]["fuel_end_liters"] == 35.0
    assert rows[0]["fuel_consumed_liters"] == 15.0


def test_closed_waybill_without_fuel_does_not_create_fake_fuel_history(
    client: TestClient,
) -> None:
    waybill_id, duty_id = _create_released_waybill(client)
    assert client.put(
        f"/api/waybills/{waybill_id}/actuals",
        json={
            "actual_departure": "2026-09-20T08:03:00",
            "actual_return": "2026-09-20T09:08:00",
            "odometer_start": 125000,
            "odometer_end": 125042,
            "fuel_start_liters": None,
            "fuel_issued_liters": None,
            "fuel_end_liters": None,
            "note": None,
        },
    ).status_code == 200
    assert client.post(f"/api/waybills/{waybill_id}/close").status_code == 200

    settings = get_settings()
    with sqlite3.connect(settings.local_database_path) as connection:
        vehicle_id_row = connection.execute(
            "SELECT vehicle_id FROM duties WHERE id = ?",
            (duty_id,),
        ).fetchone()
        assert vehicle_id_row is not None
        vehicle_id = str(vehicle_id_row[0])

    history = client.get(f"/api/vehicles/{vehicle_id}/fuel-history")
    assert history.status_code == 200
    assert history.json() == []


def test_closed_waybill_cannot_be_edited(client: TestClient) -> None:
    waybill_id, _ = _create_released_waybill(client)
    assert client.put(
        f"/api/waybills/{waybill_id}/actuals",
        json={
            "actual_departure": "2026-09-20T08:03:00",
            "actual_return": "2026-09-20T09:08:00",
            "odometer_start": 125000,
            "odometer_end": 125042,
            "fuel_start_liters": None,
            "fuel_issued_liters": None,
            "fuel_end_liters": None,
            "note": None,
        },
    ).status_code == 200
    assert client.post(f"/api/waybills/{waybill_id}/close").status_code == 200

    edit = client.put(
        f"/api/waybills/{waybill_id}/actuals",
        json={
            "actual_departure": "2026-09-20T08:05:00",
            "actual_return": "2026-09-20T09:10:00",
            "odometer_start": 125000,
            "odometer_end": 125043,
            "fuel_start_liters": None,
            "fuel_issued_liters": None,
            "fuel_end_liters": None,
            "note": "Спроба зміни",
        },
    )

    assert edit.status_code == 409
    assert "не редагується" in edit.json()["detail"]
