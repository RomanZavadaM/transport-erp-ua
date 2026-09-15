from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
from typing import Annotated, NoReturn

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from transport_erp.api.errors import ApiError
from transport_erp.config import Settings, get_settings
from transport_erp.identity.application.service import IdentityService
from transport_erp.identity.domain.errors import (
    AccountUnavailableError,
    IdentityConflictError,
    IdentityError,
    IdentityNotFoundError,
    InvalidCredentialsError,
    SessionInvalidError,
)
from transport_erp.identity.domain.models import Principal
from transport_erp.infrastructure.database import get_db_session

DbSession = Annotated[Session, Depends(get_db_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@lru_cache
def get_identity_service() -> IdentityService:
    settings = get_settings()
    return IdentityService(session_ttl_minutes=settings.session_ttl_minutes)


IdentityServiceDep = Annotated[IdentityService, Depends(get_identity_service)]


def identity_error_to_api(exc: IdentityError) -> ApiError:
    if isinstance(exc, InvalidCredentialsError):
        return ApiError(status_code=401, code=exc.code, message=exc.message)
    if isinstance(exc, SessionInvalidError):
        return ApiError(status_code=401, code=exc.code, message=exc.message)
    if isinstance(exc, AccountUnavailableError):
        return ApiError(status_code=403, code=exc.code, message=exc.message)
    if isinstance(exc, IdentityNotFoundError):
        return ApiError(status_code=404, code=exc.code, message=exc.message)
    if isinstance(exc, IdentityConflictError):
        return ApiError(status_code=409, code=exc.code, message=exc.message)
    return ApiError(status_code=422, code=exc.code, message=exc.message)


def raise_identity_error(exc: IdentityError) -> NoReturn:
    raise identity_error_to_api(exc) from exc


def get_current_principal(
    request: Request,
    session: DbSession,
    service: IdentityServiceDep,
    settings: SettingsDep,
) -> Principal:
    cookie_value = request.cookies.get(settings.session_cookie_name)
    if cookie_value is None:
        raise ApiError(
            status_code=401,
            code="SESSION_REQUIRED",
            message="Authentication is required.",
        )
    try:
        return service.authenticate_cookie(session, cookie_value)
    except IdentityError as exc:
        raise_identity_error(exc)


CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]


def require_permission(permission: str) -> Callable[..., Principal]:
    def dependency(principal: CurrentPrincipal) -> Principal:
        if permission not in principal.permissions:
            raise ApiError(
                status_code=403,
                code="PERMISSION_DENIED",
                message="Permission is required.",
                details={"permission": permission},
            )
        return principal

    return dependency
