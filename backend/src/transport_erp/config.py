from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or Path.home())
        return base / "TransportERP-UA"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "TransportERP-UA"
    base = Path(os.getenv("XDG_DATA_HOME") or (Path.home() / ".local" / "share"))
    return base / "TransportERP-UA"


class Settings(BaseSettings):
    app_name: str = "TransportERP-UA"
    environment: str = "development"
    debug: bool = False
    deployment_profile: Literal["local", "central"] = "local"
    data_dir: Path = Field(default_factory=_default_data_dir)
    documents_dir: Path | None = None
    backup_dir: Path | None = None
    frontend_dir: Path | None = None
    database_url: str | None = None
    session_ttl_minutes: int = Field(default=480, ge=5, le=10080)
    session_cookie_name: str = "transport_erp_session"
    csrf_cookie_name: str = "transport_erp_csrf"
    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict"] = "lax"
    cookie_domain: str | None = None

    model_config = SettingsConfigDict(
        env_prefix="TRANSPORT_ERP_",
        env_file=".env",
        extra="ignore",
    )

    @property
    def resolved_data_dir(self) -> Path:
        return self.data_dir.expanduser().resolve()

    @property
    def resolved_documents_dir(self) -> Path:
        value = self.documents_dir or (self.resolved_data_dir / "documents")
        return value.expanduser().resolve()

    @property
    def resolved_backup_dir(self) -> Path:
        value = self.backup_dir or (self.resolved_data_dir / "backups")
        return value.expanduser().resolve()

    @property
    def local_database_path(self) -> Path:
        return self.resolved_data_dir / "transport-erp.sqlite3"

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.deployment_profile == "local":
            return f"sqlite+pysqlite:///{self.local_database_path.as_posix()}"
        raise ValueError("central deployment requires TRANSPORT_ERP_DATABASE_URL")

    @model_validator(mode="after")
    def validate_cookie_security(self) -> Self:
        if (
            self.deployment_profile == "central"
            and self.environment.lower() == "production"
            and not self.cookie_secure
        ):
            raise ValueError("central production requires TRANSPORT_ERP_COOKIE_SECURE=true")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
