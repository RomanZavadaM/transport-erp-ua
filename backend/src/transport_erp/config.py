from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_local_data_dir() -> Path:
    if os.name == "nt":
        base = Path(os.getenv("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.getenv("XDG_DATA_HOME") or (Path.home() / ".local" / "share"))
    return base / "TransportERP-UA"


class Settings(BaseSettings):
    app_name: str = "TransportERP-UA"
    environment: str = "development"
    deployment_profile: Literal["local", "central"] = "local"
    debug: bool = False
    local_data_dir: Path = Field(default_factory=default_local_data_dir)
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

    @model_validator(mode="after")
    def resolve_profile_defaults(self) -> Self:
        self.local_data_dir = self.local_data_dir.expanduser()
        if self.database_url is None:
            db_path = self.local_data_dir / "transporterp.db"
            self.database_url = f"sqlite+pysqlite:///{db_path.as_posix()}"
        if (
            self.environment.lower() == "production"
            and self.deployment_profile == "central"
            and not self.cookie_secure
        ):
            raise ValueError("central production requires TRANSPORT_ERP_COOKIE_SECURE=true")
        return self

    @property
    def is_local_profile(self) -> bool:
        return self.deployment_profile == "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()
