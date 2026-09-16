from __future__ import annotations

import sqlite3
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from transport_erp.config import Settings


@dataclass(frozen=True)
class LocalRuntimeStatus:
    database_path: Path
    documents_path: Path
    backup_path: Path
    database_size_bytes: int
    integrity: str


@dataclass(frozen=True)
class BackupResult:
    path: Path
    size_bytes: int
    created_at: datetime


def ensure_local_storage(settings: Settings) -> None:
    if settings.deployment_profile != "local":
        return

    settings.resolved_data_dir.mkdir(parents=True, exist_ok=True)
    settings.resolved_documents_dir.mkdir(parents=True, exist_ok=True)
    settings.resolved_backup_dir.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(settings.local_database_path) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("PRAGMA busy_timeout=5000")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS companies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                edrpou TEXT,
                status TEXT NOT NULL DEFAULT 'ACTIVE'
                    CHECK (status IN ('ACTIVE', 'SUSPENDED'))
            );

            CREATE TABLE IF NOT EXISTS vehicles (
                id TEXT PRIMARY KEY,
                company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
                fleet_number TEXT NOT NULL,
                registration_number TEXT NOT NULL,
                vin TEXT,
                make TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER CHECK (year IS NULL OR year BETWEEN 1950 AND 2100),
                lifecycle_status TEXT NOT NULL DEFAULT 'ACTIVE'
                    CHECK (lifecycle_status IN ('ACTIVE','SUSPENDED','REPAIR','DECOMMISSIONED')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                row_version INTEGER NOT NULL DEFAULT 1,
                UNIQUE(company_id, fleet_number),
                UNIQUE(company_id, registration_number),
                UNIQUE(vin)
            );

            CREATE TABLE IF NOT EXISTS drivers (
                id TEXT PRIMARY KEY,
                company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
                personnel_number TEXT NOT NULL,
                last_name TEXT NOT NULL,
                first_name TEXT NOT NULL,
                middle_name TEXT,
                phone TEXT,
                employment_status TEXT NOT NULL DEFAULT 'ACTIVE'
                    CHECK (employment_status IN ('ACTIVE','LEAVE','SICK','SUSPENDED','TERMINATED')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                row_version INTEGER NOT NULL DEFAULT 1,
                UNIQUE(company_id, personnel_number)
            );

            CREATE TABLE IF NOT EXISTS stops (
                id TEXT PRIMARY KEY,
                company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
                name TEXT NOT NULL,
                locality TEXT,
                active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
                UNIQUE(company_id, name, locality)
            );

            CREATE TABLE IF NOT EXISTS routes (
                id TEXT PRIMARY KEY,
                company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE RESTRICT,
                number TEXT NOT NULL,
                name TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
                UNIQUE(company_id, number)
            );

            CREATE TABLE IF NOT EXISTS route_stops (
                route_id TEXT NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
                stop_id TEXT NOT NULL REFERENCES stops(id) ON DELETE RESTRICT,
                position INTEGER NOT NULL CHECK (position >= 1),
                PRIMARY KEY (route_id, position),
                UNIQUE(route_id, stop_id)
            );
            """
        )
        connection.execute(
            "INSERT OR IGNORE INTO app_meta(key, value) VALUES ('storage_profile', 'local-sqlite')"
        )

        company_id_row = connection.execute(
            "SELECT value FROM app_meta WHERE key = 'company_id'"
        ).fetchone()
        if company_id_row is None:
            company_id = str(uuid4())
            connection.execute(
                "INSERT INTO companies(id, name, status) VALUES (?, ?, 'ACTIVE')",
                (company_id, "Транспортне підприємство"),
            )
            connection.execute(
                "INSERT INTO app_meta(key, value) VALUES ('company_id', ?)",
                (company_id,),
            )

        connection.commit()


def get_local_status(settings: Settings) -> LocalRuntimeStatus:
    ensure_local_storage(settings)
    with sqlite3.connect(settings.local_database_path) as connection:
        row = connection.execute("PRAGMA integrity_check").fetchone()
        integrity = str(row[0]) if row is not None else "unknown"

    return LocalRuntimeStatus(
        database_path=settings.local_database_path,
        documents_path=settings.resolved_documents_dir,
        backup_path=settings.resolved_backup_dir,
        database_size_bytes=settings.local_database_path.stat().st_size,
        integrity=integrity,
    )


def create_local_backup(settings: Settings) -> BackupResult:
    ensure_local_storage(settings)
    created_at = datetime.now(UTC)
    stamp = created_at.strftime("%Y%m%d-%H%M%S")
    archive_path = settings.resolved_backup_dir / f"TransportERP-UA-backup-{stamp}.zip"

    # Build the SQLite snapshot in memory. This uses SQLite's backup API but avoids
    # a temporary database file that Windows may keep locked during cleanup.
    with sqlite3.connect(settings.local_database_path) as source:
        with sqlite3.connect(":memory:") as destination:
            source.backup(destination)
            database_bytes = destination.serialize()

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("database/transport-erp.sqlite3", database_bytes)

        for file_path in settings.resolved_documents_dir.rglob("*"):
            if file_path.is_file():
                relative = file_path.relative_to(settings.resolved_documents_dir)
                archive.write(file_path, arcname=str(Path("documents") / relative))

        archive.writestr(
            "backup-info.txt",
            "\n".join(
                [
                    "TransportERP-UA local backup",
                    f"created_at={created_at.isoformat()}",
                    f"source_database={settings.local_database_path}",
                ]
            )
            + "\n",
        )

    return BackupResult(
        path=archive_path,
        size_bytes=archive_path.stat().st_size,
        created_at=created_at,
    )


def list_local_backups(settings: Settings, limit: int = 20) -> list[BackupResult]:
    ensure_local_storage(settings)
    paths = sorted(
        settings.resolved_backup_dir.glob("TransportERP-UA-backup-*.zip"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )[:limit]

    results: list[BackupResult] = []
    for path in paths:
        stat = path.stat()
        results.append(
            BackupResult(
                path=path,
                size_bytes=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
            )
        )
    return results
