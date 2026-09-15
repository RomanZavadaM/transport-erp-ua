from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserAccount:
    id: UUID
    company_id: UUID
    username: str
    email: str | None
    status: str
    preferred_locale: str | None
    password_hash: str


@dataclass(frozen=True, slots=True)
class RoleRecord:
    id: UUID
    company_id: UUID | None
    code: str
    name: str
    system_role: bool
    active: bool


@dataclass(frozen=True, slots=True)
class Principal:
    session_id: UUID
    company_id: UUID
    user_id: UUID
    username: str
    email: str | None
    preferred_locale: str | None
    permissions: frozenset[str]


@dataclass(frozen=True, slots=True)
class SessionIssue:
    principal: Principal
    cookie_value: str
    csrf_token: str
    expires_at: datetime
