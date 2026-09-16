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


def _vehicle(client: TestClient) -> str:
    response = client.post(
        "/api/vehicles",
        json={
            "fleet_number": "501",
            "registration_number": "BC0501AA",
            "vin": "VINREPAIR501",
            "make": "Ataman",
            "model": "A092",
            "year": 2021,
            "lifecycle_status": "ACTIVE",
        },
    )
    assert response.status_code == 201
    return str(response.json()["id"])


def test_blocking_defect_marks_vehicle_for_repair(client: TestClient) -> None:
    vehicle_id = _vehicle(client)

    defect = client.post(
        f"/api/vehicles/{vehicle_id}/defects",
        json={
            "description": "Пошкодження гальмівної системи",
            "severity": "CRITICAL",
            "blocks_release": True,
            "source": "PRE_TRIP_CHECK",
            "reported_by": "Механік",
            "note": "Експлуатацію заборонено",
        },
    )

    assert defect.status_code == 201
    assert defect.json()["status"] == "OPEN"
    assert defect.json()["blocks_release"] is True

    vehicles = client.get("/api/vehicles")
    assert vehicles.status_code == 200
    assert vehicles.json()[0]["lifecycle_status"] == "REPAIR"


def test_repair_order_items_and_close_resolve_defect(client: TestClient) -> None:
    vehicle_id = _vehicle(client)
    defect = client.post(
        f"/api/vehicles/{vehicle_id}/defects",
        json={
            "description": "Несправність генератора",
            "severity": "MAJOR",
            "blocks_release": True,
            "source": "DRIVER_REPORT",
            "reported_by": "Водій",
            "note": None,
        },
    )
    assert defect.status_code == 201
    defect_id = str(defect.json()["id"])

    order = client.post(
        f"/api/vehicles/{vehicle_id}/repair-orders",
        json={
            "number": "РН-0001",
            "defect_id": defect_id,
            "description": "Діагностика та заміна генератора",
            "provider": "Власна ремонтна зона",
            "blocks_operation": True,
            "odometer_km": 150000,
        },
    )
    assert order.status_code == 201
    order_id = str(order.json()["id"])

    work = client.post(
        f"/api/repair-orders/{order_id}/items",
        json={
            "item_type": "WORK",
            "description": "Діагностика електросистеми",
            "part_number": None,
            "quantity": 2,
            "unit": "год",
            "unit_price": 400,
        },
    )
    assert work.status_code == 200

    part = client.post(
        f"/api/repair-orders/{order_id}/items",
        json={
            "item_type": "PART",
            "description": "Генератор",
            "part_number": "GEN-001",
            "quantity": 1,
            "unit": "шт",
            "unit_price": 6200,
        },
    )
    assert part.status_code == 200
    assert part.json()["total_cost"] == 7000.0

    assert client.post(f"/api/repair-orders/{order_id}/start").status_code == 200
    completed = client.post(f"/api/repair-orders/{order_id}/complete")
    assert completed.status_code == 200
    assert completed.json()["status"] == "COMPLETED"

    closed = client.post(
        f"/api/repair-orders/{order_id}/close",
        json={
            "closed_by": "Головний механік",
            "verification_comment": "Перевірено, зарядна напруга в нормі. Автобус допущено.",
        },
    )
    assert closed.status_code == 200
    assert closed.json()["status"] == "CLOSED"
    assert closed.json()["total_cost"] == 7000.0

    summary = client.get(f"/api/vehicles/{vehicle_id}/repairs")
    assert summary.status_code == 200
    assert summary.json()["defects"][0]["status"] == "RESOLVED"
    assert summary.json()["repair_orders"][0]["status"] == "CLOSED"

    vehicles = client.get("/api/vehicles")
    assert vehicles.status_code == 200
    assert vehicles.json()[0]["lifecycle_status"] == "ACTIVE"


def test_closed_repair_order_cannot_receive_more_items(client: TestClient) -> None:
    vehicle_id = _vehicle(client)
    order = client.post(
        f"/api/vehicles/{vehicle_id}/repair-orders",
        json={
            "number": "РН-0002",
            "defect_id": None,
            "description": "Поточний ремонт",
            "provider": None,
            "blocks_operation": False,
            "odometer_km": None,
        },
    )
    assert order.status_code == 201
    order_id = str(order.json()["id"])
    assert client.post(f"/api/repair-orders/{order_id}/complete").status_code == 200
    assert client.post(
        f"/api/repair-orders/{order_id}/close",
        json={"closed_by": "Механік", "verification_comment": "Ремонт перевірено"},
    ).status_code == 200

    edit = client.post(
        f"/api/repair-orders/{order_id}/items",
        json={
            "item_type": "MATERIAL",
            "description": "Мастило",
            "part_number": None,
            "quantity": 1,
            "unit": "л",
            "unit_price": 100,
        },
    )
    assert edit.status_code == 409
