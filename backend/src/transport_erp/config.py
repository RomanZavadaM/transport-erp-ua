from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TransportERP-UA"
    environment: str = "development"
    debug: bool = False

    model_config = SettingsConfigDict(
        env_prefix="TRANSPORT_ERP_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
