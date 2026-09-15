from fastapi import FastAPI

from transport_erp.api.health import router as health_router
from transport_erp.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
    )
    application.include_router(health_router)
    return application


app = create_app()
