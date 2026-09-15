from __future__ import annotations

from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TransportERP-UA"
    environment: str = "development"
    debug: bool = False
    database_url: str = (
        "postgresql+psycopg://transport_erp:transport_erp_dev@db:5432/transport_erp"
    )
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
    def validate_cookie_security(self) -> Self:
        if self.environment.lower() == "production" and not self.cookie_secure:
            raise ValueError("production requires TRANSPORT_ERP_COOKIE_SECURE=true")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
