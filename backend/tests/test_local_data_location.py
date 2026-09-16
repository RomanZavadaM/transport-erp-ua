from __future__ import annotations

from pathlib import Path

import pytest

import transport_erp.config as config
from transport_erp.config import Settings


def test_windows_data_location_does_not_depend_on_version_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    local_app_data = tmp_path / "AppData" / "Local"
    version_r1 = tmp_path / "TransportERP-UA_v0.2_TEST_r1_START"
    version_r2 = tmp_path / "TransportERP-UA_v0.2_TEST_r2_START"
    version_r1.mkdir()
    version_r2.mkdir()

    monkeypatch.setattr(config.sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
    monkeypatch.delenv("TRANSPORT_ERP_DATA_DIR", raising=False)

    monkeypatch.chdir(version_r1)
    r1_settings = Settings()

    monkeypatch.chdir(version_r2)
    r2_settings = Settings()

    expected_data_dir = (local_app_data / "TransportERP-UA").resolve()
    expected_database = expected_data_dir / "transport-erp.sqlite3"

    assert r1_settings.resolved_data_dir == expected_data_dir
    assert r2_settings.resolved_data_dir == expected_data_dir
    assert r1_settings.local_database_path == expected_database
    assert r2_settings.local_database_path == expected_database
