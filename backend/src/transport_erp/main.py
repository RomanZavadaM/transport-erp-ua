from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from transport_erp.api.catalogs import router as catalogs_router
from transport_erp.api.details import router as details_router
from transport_erp.api.errors import ApiError, api_error_handler
from transport_erp.api.fleet import router as fleet_router
from transport_erp.api.health import router as health_router
from transport_erp.api.local import router as local_router
from transport_erp.api.security import SecurityContextMiddleware
from transport_erp.config import get_settings
from transport_erp.identity.api.router import router as identity_router
from transport_erp.local_runtime import ensure_local_storage


def create_app() -> FastAPI:
    settings = get_settings()
    ensure_local_storage(settings)

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
    )
    application.add_exception_handler(ApiError, api_error_handler)
    application.add_middleware(SecurityContextMiddleware, settings=settings)
    application.include_router(health_router)
    application.include_router(local_router)
    application.include_router(fleet_router)
    application.include_router(details_router)
    application.include_router(catalogs_router)
    application.include_router(identity_router)

    if settings.frontend_dir is not None:
        frontend_dir = settings.frontend_dir.expanduser().resolve()
        if (frontend_dir / "index.html").exists():
            application.mount(
                "/",
                StaticFiles(directory=frontend_dir, html=True),
                name="frontend",
            )

    return application


app = create_app()
