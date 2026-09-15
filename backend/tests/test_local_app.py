from __future__ import annotations

import zipfile
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
def local_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("TRANSPORT_ERP_DEPLOYMENT_PROFILE", "local")
    monkeypatch.setenv("TRANSPORT_ERP_ENVIRONMENT", "test")
    monkeypatch.setenv("TRANSPORT_ERP_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("TRANSPORT_ERP_DATABASE_URL", raising=False)
    monkeypatch.delenv("TRANSPORT_ERP_FRONTEND_DIR", raising=False)
    _clear_runtime_caches()
    client = TestClient(create_app())
    yield client
    client.close()
    _clear_runtime_caches()


def test_local_status_and_backup(local_client: TestClient) -> None:
    status_response = local_client.get("/api/local/status")
    assert status_response.status_code == 200
    status = status_response.json()
    assert status["profile"] == "local"
    assert status["integrity"] == "ok"

    documents_path = Path(status["documents_path"])
    documents_path.joinpath("sample.txt").write_text("document", encoding="utf-8")

    backup_response = local_client.post("/api/local/backup")
    assert backup_response.status_code == 200
    backup_path = Path(backup_response.json()["path"])
    assert backup_path.exists()

    with zipfile.ZipFile(backup_path) as archive:
        names = set(archive.namelist())
        assert "database/transport-erp.sqlite3" in names
        assert "documents/sample.txt" in names
        assert "backup-info.txt" in names

    backups_response = local_client.get("/api/local/backups")
    assert backups_response.status_code == 200
    assert backups_response.json()[0]["path"] == str(backup_path)


def test_vehicle_create_list_and_update(local_client: TestClient) -> None:
    payload = {
        "fleet_number": "101",
        "registration_number": "BC1234AA",
        "vin": "TESTVIN101",
        "make": "Ataman",
        "model": "A092",
        "year": 2020,
        "lifecycle_status": "ACTIVE",
    }
    created = local_client.post("/api/vehicles", json=payload)
    assert created.status_code == 201
    vehicle_id = created.json()["id"]

    listed = local_client.get("/api/vehicles")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["fleet_number"] == "101"

    payload["lifecycle_status"] = "REPAIR"
    updated = local_client.put(f"/api/vehicles/{vehicle_id}", json=payload)
    assert updated.status_code == 200
    assert updated.json()["lifecycle_status"] == "REPAIR"
    assert updated.json()["row_version"] == 2


def test_driver_create_list_and_update(local_client: TestClient) -> None:
    payload = {
        "personnel_number": "D-001",
        "last_name": "Іваненко",
        "first_name": "Іван",
        "middle_name": "Іванович",
        "phone": "+380670000000",
        "employment_status": "ACTIVE",
    }
    created = local_client.post("/api/drivers", json=payload)
    assert created.status_code == 201
    driver_id = created.json()["id"]

    listed = local_client.get("/api/drivers")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["last_name"] == "Іваненко"

    payload["employment_status"] = "LEAVE"
    updated = local_client.put(f"/api/drivers/{driver_id}", json=payload)
    assert updated.status_code == 200
    assert updated.json()["employment_status"] == "LEAVE"
    assert updated.json()["row_version"] == 2


def test_company_settings(local_client: TestClient) -> None:
    initial = local_client.get("/api/company")
    assert initial.status_code == 200

    updated = local_client.put(
        "/api/company",
        json={"name": "АТП Завада", "edrpou": "12345678"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "АТП Завада"
    assert updated.json()["edrpou"] == "12345678"


def test_stops_and_ordered_route(local_client: TestClient) -> None:
    first = local_client.post(
        "/api/stops", json={"name": "Автовокзал", "locality": "Львів", "active": True}
    )
    second = local_client.post(
        "/api/stops", json={"name": "Центр", "locality": "Львів", "active": True}
    )
    third = local_client.post(
        "/api/stops", json={"name": "Залізничний вокзал", "locality": "Львів", "active": True}
    )
    assert first.status_code == second.status_code == third.status_code == 201

    stop_ids = [first.json()["id"], second.json()["id"], third.json()["id"]]
    created = local_client.post(
        "/api/routes",
        json={
            "number": "1",
            "name": "Автовокзал — Вокзал",
            "active": True,
            "stop_ids": stop_ids,
        },
    )
    assert created.status_code == 201
    assert [item["name"] for item in created.json()["stops"]] == [
        "Автовокзал",
        "Центр",
        "Залізничний вокзал",
    ]

    route_id = created.json()["id"]
    updated = local_client.put(
        f"/api/routes/{route_id}",
        json={
            "number": "1",
            "name": "Автовокзал — Вокзал",
            "active": True,
            "stop_ids": list(reversed(stop_ids)),
        },
    )
    assert updated.status_code == 200
    assert [item["name"] for item in updated.json()["stops"]] == [
        "Залізничний вокзал",
        "Центр",
        "Автовокзал",
    ]
