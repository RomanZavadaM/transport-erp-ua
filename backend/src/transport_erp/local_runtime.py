from __future__ import annotations

import sqlite3
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

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
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "INSERT OR IGNORE INTO app_meta(key, value) VALUES ('storage_profile', 'local-sqlite')"
        )
        connection.commit()


def get_local_status(settings: Settings) -> LocalRuntimeStatus:
    ensure_local_storage(settings)
    with sqlite3.connect(settings.local_database_path) as connection:
        integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])

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

    with tempfile.TemporaryDirectory(prefix="transport-erp-backup-") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        database_copy = temp_dir / "transport-erp.sqlite3"

        with sqlite3.connect(settings.local_database_path) as source:
            with sqlite3.connect(database_copy) as destination:
                source.backup(destination)

        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(database_copy, arcname="database/transport-erp.sqlite3")

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
