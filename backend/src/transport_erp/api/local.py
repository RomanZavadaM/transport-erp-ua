from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from transport_erp.config import get_settings
from transport_erp.local_runtime import create_local_backup, get_local_status, list_local_backups

router = APIRouter(prefix="/local", tags=["Local runtime"])


class LocalStatusResponse(BaseModel):
    profile: str
    database_path: str
    documents_path: str
    backup_path: str
    database_size_bytes: int
    integrity: str


class BackupResponse(BaseModel):
    path: str
    size_bytes: int
    created_at: datetime


def _require_local() -> None:
    if get_settings().deployment_profile != "local":
        raise HTTPException(status_code=404, detail="Local runtime is disabled")


@router.get("/status", response_model=LocalStatusResponse)
def status() -> LocalStatusResponse:
    _require_local()
    result = get_local_status(get_settings())
    return LocalStatusResponse(
        profile="local",
        database_path=str(result.database_path),
        documents_path=str(result.documents_path),
        backup_path=str(result.backup_path),
        database_size_bytes=result.database_size_bytes,
        integrity=result.integrity,
    )


@router.post("/backup", response_model=BackupResponse)
def create_backup() -> BackupResponse:
    _require_local()
    result = create_local_backup(get_settings())
    return BackupResponse(
        path=str(result.path),
        size_bytes=result.size_bytes,
        created_at=result.created_at,
    )


@router.get("/backups", response_model=list[BackupResponse])
def backups() -> list[BackupResponse]:
    _require_local()
    return [
        BackupResponse(path=str(item.path), size_bytes=item.size_bytes, created_at=item.created_at)
        for item in list_local_backups(get_settings())
    ]
