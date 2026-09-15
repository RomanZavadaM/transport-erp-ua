from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status

from transport_erp.config import Settings
from transport_erp.identity.api.dependencies import (
    CurrentPrincipal,
    DbSession,
    IdentityServiceDep,
    SettingsDep,
    raise_identity_error,
    require_permission,
)
from transport_erp.identity.api.schemas import (
    AuthMeData,
    AuthMeResponse,
    LoginRequest,
    PermissionsResponse,
    ResponseMeta,
    RoleCreateRequest,
    RoleListResponse,
    RoleResponse,
    RoleView,
    UserCreateRequest,
    UserListResponse,
    UserPatchRequest,
    UserResponse,
    UserRolesData,
    UserRolesReplaceRequest,
    UserRolesResponse,
    UserView,
)
from transport_erp.identity.domain.errors import IdentityError
from transport_erp.identity.domain.models import Principal, RoleRecord, SessionIssue, UserAccount

router = APIRouter(prefix="/api/v1")


def _meta(request: Request) -> ResponseMeta:
    return ResponseMeta(request_id=str(getattr(request.state, "request_id", "")))


def _user_view(user: UserAccount) -> UserView:
    return UserView(
        id=user.id,
        company_id=user.company_id,
        username=user.username,
        email=user.email,
        status=user.status,
        preferred_locale=user.preferred_locale,
    )


def _principal_data(principal: Principal) -> AuthMeData:
    return AuthMeData(
        user=UserView(
            id=principal.user_id,
            company_id=principal.company_id,
            username=principal.username,
            email=principal.email,
            status="ACTIVE",
            preferred_locale=principal.preferred_locale,
        ),
        permissions=sorted(principal.permissions),
    )


def _role_view(role: RoleRecord) -> RoleView:
    return RoleView(
        id=role.id,
        company_id=role.company_id,
        code=role.code,
        name=role.name,
        system_role=role.system_role,
        active=role.active,
    )


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client is not None else None


def _set_session_cookies(
    response: Response, issue: SessionIssue, settings: Settings
) -> None:
    max_age = settings.session_ttl_minutes * 60
    response.set_cookie(
        key=settings.session_cookie_name,
        value=issue.cookie_value,
        max_age=max_age,
        expires=issue.expires_at,
        path="/api/v1",
        domain=settings.cookie_domain,
        secure=settings.cookie_secure,
        httponly=True,
        samesite=settings.cookie_samesite,
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=issue.csrf_token,
        max_age=max_age,
        expires=issue.expires_at,
        path="/api/v1",
        domain=settings.cookie_domain,
        secure=settings.cookie_secure,
        httponly=False,
        samesite=settings.cookie_samesite,
    )


def _clear_session_cookies(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        settings.session_cookie_name,
        path="/api/v1",
        domain=settings.cookie_domain,
    )
    response.delete_cookie(
        settings.csrf_cookie_name,
        path="/api/v1",
        domain=settings.cookie_domain,
    )


@router.post("/auth/login", response_model=AuthMeResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: DbSession,
    service: IdentityServiceDep,
    settings: SettingsDep,
) -> AuthMeResponse:
    try:
        issue = service.login(
            session,
            company_edrpou=payload.company_edrpou,
            username=payload.username,
            password=payload.password.get_secret_value(),
            ip_address=_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
    except IdentityError as exc:
        raise_identity_error(exc)
    _set_session_cookies(response, issue, settings)
    return AuthMeResponse(data=_principal_data(issue.principal), meta=_meta(request))


@router.post("/auth/refresh", response_model=AuthMeResponse)
def refresh_session(
    request: Request,
    response: Response,
    principal: CurrentPrincipal,
    session: DbSession,
    service: IdentityServiceDep,
    settings: SettingsDep,
) -> AuthMeResponse:
    try:
        issue = service.rotate_session(
            session,
            principal=principal,
            ip_address=_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
    except IdentityError as exc:
        raise_identity_error(exc)
    _set_session_cookies(response, issue, settings)
    return AuthMeResponse(data=_principal_data(issue.principal), meta=_meta(request))


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    principal: CurrentPrincipal,
    session: DbSession,
    service: IdentityServiceDep,
    settings: SettingsDep,
) -> None:
    try:
        service.logout(session, principal)
    except IdentityError as exc:
        raise_identity_error(exc)
    _clear_session_cookies(response, settings)


@router.get("/auth/me", response_model=AuthMeResponse)
def me(request: Request, principal: CurrentPrincipal) -> AuthMeResponse:
    return AuthMeResponse(data=_principal_data(principal), meta=_meta(request))


@router.get("/auth/permissions", response_model=PermissionsResponse)
def my_permissions(request: Request, principal: CurrentPrincipal) -> PermissionsResponse:
    return PermissionsResponse(data=sorted(principal.permissions), meta=_meta(request))


@router.get("/users", response_model=UserListResponse)
def list_users(
    request: Request,
    session: DbSession,
    service: IdentityServiceDep,
    principal: Annotated[Principal, Depends(require_permission("user.read"))],
) -> UserListResponse:
    try:
        users = service.list_users(session, principal)
    except IdentityError as exc:
        raise_identity_error(exc)
    return UserListResponse(data=[_user_view(user) for user in users], meta=_meta(request))


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    request: Request,
    session: DbSession,
    service: IdentityServiceDep,
    principal: Annotated[Principal, Depends(require_permission("user.create"))],
) -> UserResponse:
    try:
        user = service.create_user(
            session,
            principal=principal,
            username=payload.username,
            email=payload.email,
            password=payload.password.get_secret_value(),
            preferred_locale=payload.preferred_locale,
        )
    except IdentityError as exc:
        raise_identity_error(exc)
    return UserResponse(data=_user_view(user), meta=_meta(request))


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    request: Request,
    session: DbSession,
    service: IdentityServiceDep,
    principal: Annotated[Principal, Depends(require_permission("user.read"))],
) -> UserResponse:
    try:
        user = service.get_user(session, principal, user_id)
    except IdentityError as exc:
        raise_identity_error(exc)
    return UserResponse(data=_user_view(user), meta=_meta(request))


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    payload: UserPatchRequest,
    request: Request,
    session: DbSession,
    service: IdentityServiceDep,
    principal: Annotated[Principal, Depends(require_permission("user.update"))],
) -> UserResponse:
    try:
        user = service.update_user_profile(
            session,
            principal=principal,
            user_id=user_id,
            email_is_set="email" in payload.model_fields_set,
            email=payload.email,
            locale_is_set="preferred_locale" in payload.model_fields_set,
            preferred_locale=payload.preferred_locale,
        )
    except IdentityError as exc:
        raise_identity_error(exc)
    return UserResponse(data=_user_view(user), meta=_meta(request))


@router.post("/users/{user_id}/activate", response_model=UserResponse)
def activate_user(
    user_id: UUID,
    request: Request,
    session: DbSession,
    service: IdentityServiceDep,
    principal: Annotated[Principal, Depends(require_permission("user.status.change"))],
) -> UserResponse:
    try:
        user = service.set_user_status(
            session, principal=principal, user_id=user_id, status="ACTIVE"
        )
    except IdentityError as exc:
        raise_identity_error(exc)
    return UserResponse(data=_user_view(user), meta=_meta(request))


@router.post("/users/{user_id}/suspend", response_model=UserResponse)
def suspend_user(
    user_id: UUID,
    request: Request,
    session: DbSession,
    service: IdentityServiceDep,
    principal: Annotated[Principal, Depends(require_permission("user.status.change"))],
) -> UserResponse:
    try:
        user = service.set_user_status(
            session, principal=principal, user_id=user_id, status="SUSPENDED"
        )
    except IdentityError as exc:
        raise_identity_error(exc)
    return UserResponse(data=_user_view(user), meta=_meta(request))


@router.get("/users/{user_id}/roles", response_model=UserRolesResponse)
def get_user_roles(
    user_id: UUID,
    request: Request,
    session: DbSession,
    service: IdentityServiceDep,
    principal: Annotated[Principal, Depends(require_permission("user.read"))],
) -> UserRolesResponse:
    try:
        roles = service.get_user_roles(session, principal, user_id)
    except IdentityError as exc:
        raise_identity_error(exc)
    return UserRolesResponse(
        data=UserRolesData(user_id=user_id, roles=roles),
        meta=_meta(request),
    )


@router.put("/users/{user_id}/roles", response_model=UserRolesResponse)
def replace_user_roles(
    user_id: UUID,
    payload: UserRolesReplaceRequest,
    request: Request,
    session: DbSession,
    service: IdentityServiceDep,
    principal: Annotated[Principal, Depends(require_permission("user.roles.manage"))],
) -> UserRolesResponse:
    try:
        roles = service.replace_user_roles(
            session,
            principal=principal,
            user_id=user_id,
            role_ids=payload.role_ids,
        )
    except IdentityError as exc:
        raise_identity_error(exc)
    return UserRolesResponse(
        data=UserRolesData(user_id=user_id, roles=roles),
        meta=_meta(request),
    )


@router.get("/roles", response_model=RoleListResponse)
def list_roles(
    request: Request,
    session: DbSession,
    service: IdentityServiceDep,
    principal: Annotated[Principal, Depends(require_permission("role.read"))],
) -> RoleListResponse:
    try:
        roles = service.list_roles(session, principal)
    except IdentityError as exc:
        raise_identity_error(exc)
    return RoleListResponse(data=[_role_view(role) for role in roles], meta=_meta(request))


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreateRequest,
    request: Request,
    session: DbSession,
    service: IdentityServiceDep,
    principal: Annotated[Principal, Depends(require_permission("role.manage"))],
) -> RoleResponse:
    try:
        role = service.create_role(
            session,
            principal=principal,
            code=payload.code,
            name=payload.name,
            permission_codes=payload.permissions,
        )
    except IdentityError as exc:
        raise_identity_error(exc)
    return RoleResponse(data=_role_view(role), meta=_meta(request))


@router.get("/permissions", response_model=PermissionsResponse)
def list_permission_catalog(
    request: Request,
    session: DbSession,
    service: IdentityServiceDep,
    principal: Annotated[Principal, Depends(require_permission("permission.read"))],
) -> PermissionsResponse:
    try:
        permissions = service.list_permissions(session, principal)
    except IdentityError as exc:
        raise_identity_error(exc)
    return PermissionsResponse(data=permissions, meta=_meta(request))
