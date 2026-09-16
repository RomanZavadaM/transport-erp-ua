from __future__ import annotations

from fastapi.testclient import TestClient

from tests.test_local_app import _create_vehicle, local_client as _local_client  # noqa: F401


def _set_odometer(client: TestClient, vehicle_id: str, reading: int) -> None:
    response = client.post(
        f"/api/vehicles/{vehicle_id}/odometer",
        json={"reading_km": reading, "note": "Контрольний пробіг"},
    )
    assert response.status_code == 201


def test_stoir_uses_existing_vehicle_odometer(_local_client: TestClient) -> None:
    vehicle_id = _create_vehicle(_local_client)
    _set_odometer(_local_client, vehicle_id, 104_600)

    created = _local_client.post(
        f"/api/vehicles/{vehicle_id}/stoir/plans",
        json={
            "plan_kind": "MAINTENANCE",
            "code": "TO-1",
            "name": "Технічне обслуговування №1",
            "basis_source": "MANUFACTURER",
            "interval_km": 5000,
            "interval_months": None,
            "last_completed_date": None,
            "last_completed_odometer": 100000,
            "warning_km": 500,
            "warning_days": 14,
            "note": "Інтервал за документацією виробника",
        },
    )

    assert created.status_code == 201
    body = created.json()
    assert body["current_odometer"] == 104600
    assert body["next_due_odometer"] == 105000
    assert body["remaining_km"] == 400
    assert body["state"] == "DUE_SOON"


def test_quarterly_inspection_plan_calculates_next_date(_local_client: TestClient) -> None:
    vehicle_id = _create_vehicle(_local_client)

    created = _local_client.post(
        f"/api/vehicles/{vehicle_id}/stoir/plans",
        json={
            "plan_kind": "INSPECTION",
            "code": "Q-INSP",
            "name": "Щоквартальна перевірка технічного стану",
            "basis_source": "NORMATIVE",
            "interval_km": None,
            "interval_months": 3,
            "last_completed_date": "2026-07-01",
            "last_completed_odometer": None,
            "warning_km": 500,
            "warning_days": 20,
            "note": "Планова перевірка пасажирського КТЗ",
        },
    )

    assert created.status_code == 201
    assert created.json()["next_due_date"] == "2026-10-01"


def test_completed_maintenance_advances_mileage_and_writes_history(
    _local_client: TestClient,
) -> None:
    vehicle_id = _create_vehicle(_local_client)
    _set_odometer(_local_client, vehicle_id, 104_700)
    created = _local_client.post(
        f"/api/vehicles/{vehicle_id}/stoir/plans",
        json={
            "plan_kind": "MAINTENANCE",
            "code": "TO-1",
            "name": "ТО-1",
            "basis_source": "MANUFACTURER",
            "interval_km": 5000,
            "interval_months": None,
            "last_completed_date": None,
            "last_completed_odometer": 100000,
            "warning_km": 500,
            "warning_days": 14,
            "note": None,
        },
    )
    assert created.status_code == 201
    plan_id = created.json()["id"]

    completed = _local_client.post(
        f"/api/stoir/plans/{plan_id}/complete",
        json={
            "completed_date": "2026-09-16",
            "odometer_km": 104700,
            "outcome": "COMPLETED",
            "performed_by": "Петренко П.П.",
            "provider": "Власна ремонтна зона",
            "document_number": "ТО-1/2026-0916",
            "document_valid_until": None,
            "comment": "Виконано за регламентом",
        },
    )

    assert completed.status_code == 200
    summary = completed.json()
    assert summary["plans"][0]["last_completed_odometer"] == 104700
    assert summary["plans"][0]["next_due_odometer"] == 109700
    assert len(summary["history"]) == 1
    event = summary["history"][0]
    assert event["document_number"] == "ТО-1/2026-0916"
    assert event["provider"] == "Власна ремонтна зона"
    assert event["outcome"] == "COMPLETED"


def test_otk_protocol_validity_becomes_next_due_date(_local_client: TestClient) -> None:
    vehicle_id = _create_vehicle(_local_client)
    created = _local_client.post(
        f"/api/vehicles/{vehicle_id}/stoir/plans",
        json={
            "plan_kind": "OTK",
            "code": "OTK",
            "name": "Обов'язковий технічний контроль",
            "basis_source": "NORMATIVE",
            "interval_km": None,
            "interval_months": 12,
            "last_completed_date": "2025-09-20",
            "last_completed_odometer": None,
            "warning_km": 500,
            "warning_days": 30,
            "note": None,
        },
    )
    assert created.status_code == 201
    plan_id = created.json()["id"]

    completed = _local_client.post(
        f"/api/stoir/plans/{plan_id}/complete",
        json={
            "completed_date": "2026-09-20",
            "odometer_km": None,
            "outcome": "PASSED",
            "performed_by": None,
            "provider": "Пункт ОТК",
            "document_number": "UA-OTK-123456",
            "document_valid_until": "2027-03-20",
            "comment": None,
        },
    )

    assert completed.status_code == 200
    plan = completed.json()["plans"][0]
    assert plan["next_due_date"] == "2027-03-20"
    history = completed.json()["history"]
    assert history[0]["document_number"] == "UA-OTK-123456"
    assert history[0]["document_valid_until"] == "2027-03-20"
