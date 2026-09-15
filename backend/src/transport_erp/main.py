from fastapi import FastAPI

from transport_erp.api.errors import ApiError, api_error_handler
from transport_erp.api.health import router as health_router
from transport_erp.api.security import SecurityContextMiddleware
from transport_erp.config import get_settings
from transport_erp.identity.api.router import router as identity_router


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
    )
    application.add_exception_handler(ApiError, api_error_handler)
    application.add_middleware(SecurityContextMiddleware, settings=settings)
    application.include_router(health_router)
    application.include_router(identity_router)
    return application


app = create_app()
