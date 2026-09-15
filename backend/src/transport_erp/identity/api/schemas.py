from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, SecretStr

LocaleCode = Literal["uk", "en", "es", "fr", "de"]


class ResponseMeta(BaseModel):
    request_id: str


class LoginRequest(BaseModel):
    company_edrpou: str = Field(min_length=8, max_length=10, pattern=r"^\d{8,10}$")
    username: str = Field(min_length=1, max_length=100)
    password: SecretStr


class UserView(BaseModel):
    id: UUID
    company_id: UUID
    username: str
    email: str | None
    status: str
    preferred_locale: str | None


class AuthMeData(BaseModel):
    user: UserView
    permissions: list[str]


class AuthMeResponse(BaseModel):
    data: AuthMeData
    meta: ResponseMeta


class PermissionsResponse(BaseModel):
    data: list[str]
    meta: ResponseMeta


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=320)
    password: SecretStr
    preferred_locale: LocaleCode | None = None


class UserPatchRequest(BaseModel):
    email: str | None = Field(default=None, max_length=320)
    preferred_locale: LocaleCode | None = None


class UserResponse(BaseModel):
    data: UserView
    meta: ResponseMeta


class UserListResponse(BaseModel):
    data: list[UserView]
    meta: ResponseMeta


class UserRolesReplaceRequest(BaseModel):
    role_ids: list[UUID] = Field(default_factory=list)


class UserRolesData(BaseModel):
    user_id: UUID
    roles: list[str]


class UserRolesResponse(BaseModel):
    data: UserRolesData
    meta: ResponseMeta


class RoleView(BaseModel):
    id: UUID
    company_id: UUID | None
    code: str
    name: str
    system_role: bool
    active: bool


class RoleListResponse(BaseModel):
    data: list[RoleView]
    meta: ResponseMeta


class RoleCreateRequest(BaseModel):
    code: str = Field(
        min_length=2,
        max_length=80,
        pattern=r"^[A-Za-z][A-Za-z0-9_.-]{1,79}$",
    )
    name: str = Field(min_length=1, max_length=200)
    permissions: list[str] = Field(default_factory=list)


class RoleResponse(BaseModel):
    data: RoleView
    meta: ResponseMeta
