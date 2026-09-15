from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from transport_erp.identity.domain.models import RoleRecord, UserAccount


def _is_sqlite(session: Session) -> bool:
    return session.get_bind().dialect.name == "sqlite"


def _db_uuid(session: Session, value: UUID | None) -> UUID | str | None:
    if value is None:
        return None
    return str(value) if _is_sqlite(session) else value


def _db_datetime(session: Session, value: datetime) -> datetime | str:
    if not _is_sqlite(session):
        return value
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _uuid(value: object | None) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


class IdentityRepository:
    def resolve_company_id(self, session: Session, edrpou: str) -> UUID | None:
        if _is_sqlite(session):
            value = session.execute(
                text(
                    """
                    SELECT id
                    FROM companies
                    WHERE edrpou = :edrpou AND status = 'ACTIVE'
                    LIMIT 1
                    """
                ),
                {"edrpou": edrpou},
            ).scalar_one_or_none()
        else:
            value = session.execute(
                text("SELECT auth_resolve_company_id(:edrpou)"),
                {"edrpou": edrpou},
            ).scalar_one_or_none()
        return _uuid(value)

    def get_user_by_username(
        self, session: Session, company_id: UUID, username: str
    ) -> UserAccount | None:
        row = session.execute(
            text(
                """
                SELECT id, company_id, username, email,
                       status, preferred_locale, password_hash
                FROM users
                WHERE company_id = :company_id AND username = :username
                """
            ),
            {"company_id": _db_uuid(session, company_id), "username": username},
        ).mappings().one_or_none()
        return self._user_from_row(row) if row is not None else None

    def get_user_by_id(
        self, session: Session, company_id: UUID, user_id: UUID
    ) -> UserAccount | None:
        row = session.execute(
            text(
                """
                SELECT id, company_id, username, email,
                       status, preferred_locale, password_hash
                FROM users
                WHERE company_id = :company_id AND id = :user_id
                """
            ),
            {
                "company_id": _db_uuid(session, company_id),
                "user_id": _db_uuid(session, user_id),
            },
        ).mappings().one_or_none()
        return self._user_from_row(row) if row is not None else None

    def get_active_session_user(
        self, session: Session, company_id: UUID, token_hash: str
    ) -> tuple[UUID, UserAccount] | None:
        now = datetime.now(UTC)
        row = session.execute(
            text(
                """
                SELECT s.id AS session_id,
                       u.id, u.company_id, u.username,
                       u.email, u.status, u.preferred_locale, u.password_hash
                FROM user_sessions s
                JOIN users u
                  ON u.company_id = s.company_id AND u.id = s.user_id
                JOIN companies c ON c.id = s.company_id
                WHERE s.company_id = :company_id
                  AND s.token_hash = :token_hash
                  AND s.revoked_at IS NULL
                  AND s.expires_at > :now
                  AND u.status = 'ACTIVE'
                  AND c.status = 'ACTIVE'
                """
            ),
            {
                "company_id": _db_uuid(session, company_id),
                "token_hash": token_hash,
                "now": _db_datetime(session, now),
            },
        ).mappings().one_or_none()
        if row is None:
            return None
        session_id = _uuid(row["session_id"])
        assert session_id is not None
        return session_id, self._user_from_row(row)

    def effective_permissions(
        self, session: Session, company_id: UUID, user_id: UUID
    ) -> frozenset[str]:
        rows = session.execute(
            text(
                """
                SELECT DISTINCT p.code
                FROM user_roles ur
                JOIN roles r ON r.id = ur.role_id
                JOIN role_permissions rp ON rp.role_id = r.id
                JOIN permissions p ON p.id = rp.permission_id
                WHERE ur.company_id = :company_id
                  AND ur.user_id = :user_id
                  AND r.active = true
                  AND (r.company_id IS NULL OR r.company_id = :company_id)
                ORDER BY p.code
                """
            ),
            {
                "company_id": _db_uuid(session, company_id),
                "user_id": _db_uuid(session, user_id),
            },
        ).scalars().all()
        return frozenset(str(value) for value in rows)

    def create_session(
        self,
        session: Session,
        *,
        company_id: UUID,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
        rotated_from_id: UUID | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> UUID:
        session_id = uuid4()
        ip_expression = ":ip_address" if _is_sqlite(session) else "CAST(:ip_address AS inet)"
        session.execute(
            text(
                f"""
                INSERT INTO user_sessions (
                    id, company_id, user_id, token_hash, expires_at,
                    rotated_from_id, ip_address, user_agent
                )
                VALUES (
                    :id, :company_id, :user_id, :token_hash, :expires_at,
                    :rotated_from_id, {ip_expression}, :user_agent
                )
                """
            ),
            {
                "id": _db_uuid(session, session_id),
                "company_id": _db_uuid(session, company_id),
                "user_id": _db_uuid(session, user_id),
                "token_hash": token_hash,
                "expires_at": _db_datetime(session, expires_at),
                "rotated_from_id": _db_uuid(session, rotated_from_id),
                "ip_address": ip_address,
                "user_agent": user_agent,
            },
        )
        return session_id

    def revoke_session(self, session: Session, company_id: UUID, session_id: UUID) -> bool:
        result = session.execute(
            text(
                """
                UPDATE user_sessions
                SET revoked_at = :revoked_at
                WHERE company_id = :company_id
                  AND id = :session_id
                  AND revoked_at IS NULL
                """
            ),
            {
                "revoked_at": _db_datetime(session, datetime.now(UTC)),
                "company_id": _db_uuid(session, company_id),
                "session_id": _db_uuid(session, session_id),
            },
        )
        return result.rowcount > 0

    def update_last_login(self, session: Session, company_id: UUID, user_id: UUID) -> None:
        now = _db_datetime(session, datetime.now(UTC))
        session.execute(
            text(
                """
                UPDATE users
                SET last_login_at = :now, updated_at = :now, row_version = row_version + 1
                WHERE company_id = :company_id AND id = :user_id
                """
            ),
            {
                "now": now,
                "company_id": _db_uuid(session, company_id),
                "user_id": _db_uuid(session, user_id),
            },
        )

    def update_password_hash(
        self, session: Session, company_id: UUID, user_id: UUID, password_hash: str
    ) -> None:
        session.execute(
            text(
                """
                UPDATE users
                SET password_hash = :password_hash,
                    updated_at = :updated_at, row_version = row_version + 1
                WHERE company_id = :company_id AND id = :user_id
                """
            ),
            {
                "company_id": _db_uuid(session, company_id),
                "user_id": _db_uuid(session, user_id),
                "password_hash": password_hash,
                "updated_at": _db_datetime(session, datetime.now(UTC)),
            },
        )

    def list_users(self, session: Session, company_id: UUID) -> list[UserAccount]:
        rows = session.execute(
            text(
                """
                SELECT id, company_id, username, email,
                       status, preferred_locale, password_hash
                FROM users
                WHERE company_id = :company_id
                ORDER BY username
                """
            ),
            {"company_id": _db_uuid(session, company_id)},
        ).mappings().all()
        return [self._user_from_row(row) for row in rows]

    def create_user(
        self,
        session: Session,
        *,
        company_id: UUID,
        username: str,
        email: str | None,
        password_hash: str,
        preferred_locale: str | None,
        actor_user_id: UUID,
    ) -> UserAccount:
        user_id = uuid4()
        row = session.execute(
            text(
                """
                INSERT INTO users (
                    id, company_id, username, email, password_hash, preferred_locale,
                    created_by, updated_by
                )
                VALUES (
                    :id, :company_id, :username, :email, :password_hash, :preferred_locale,
                    :actor_user_id, :actor_user_id
                )
                RETURNING id, company_id, username, email,
                          status, preferred_locale, password_hash
                """
            ),
            {
                "id": _db_uuid(session, user_id),
                "company_id": _db_uuid(session, company_id),
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "preferred_locale": preferred_locale,
                "actor_user_id": _db_uuid(session, actor_user_id),
            },
        ).mappings().one()
        return self._user_from_row(row)

    def update_user_profile(
        self,
        session: Session,
        *,
        company_id: UUID,
        user_id: UUID,
        email: str | None,
        preferred_locale: str | None,
        actor_user_id: UUID,
    ) -> UserAccount | None:
        row = session.execute(
            text(
                """
                UPDATE users
                SET email = :email,
                    preferred_locale = :preferred_locale,
                    updated_at = :updated_at, updated_by = :actor_user_id,
                    row_version = row_version + 1
                WHERE company_id = :company_id AND id = :user_id
                RETURNING id, company_id, username, email,
                          status, preferred_locale, password_hash
                """
            ),
            {
                "company_id": _db_uuid(session, company_id),
                "user_id": _db_uuid(session, user_id),
                "email": email,
                "preferred_locale": preferred_locale,
                "actor_user_id": _db_uuid(session, actor_user_id),
                "updated_at": _db_datetime(session, datetime.now(UTC)),
            },
        ).mappings().one_or_none()
        return self._user_from_row(row) if row is not None else None

    def set_user_status(
        self,
        session: Session,
        *,
        company_id: UUID,
        user_id: UUID,
        status: str,
        actor_user_id: UUID,
    ) -> UserAccount | None:
        row = session.execute(
            text(
                """
                UPDATE users
                SET status = :status,
                    updated_at = :updated_at, updated_by = :actor_user_id,
                    row_version = row_version + 1
                WHERE company_id = :company_id AND id = :user_id
                RETURNING id, company_id, username, email,
                          status, preferred_locale, password_hash
                """
            ),
            {
                "company_id": _db_uuid(session, company_id),
                "user_id": _db_uuid(session, user_id),
                "status": status,
                "actor_user_id": _db_uuid(session, actor_user_id),
                "updated_at": _db_datetime(session, datetime.now(UTC)),
            },
        ).mappings().one_or_none()
        return self._user_from_row(row) if row is not None else None

    def role_codes_for_user(
        self, session: Session, company_id: UUID, user_id: UUID
    ) -> list[str]:
        rows = session.execute(
            text(
                """
                SELECT r.code
                FROM user_roles ur
                JOIN roles r ON r.id = ur.role_id
                WHERE ur.company_id = :company_id
                  AND ur.user_id = :user_id
                  AND r.active = true
                  AND (r.company_id IS NULL OR r.company_id = :company_id)
                ORDER BY r.code
                """
            ),
            {
                "company_id": _db_uuid(session, company_id),
                "user_id": _db_uuid(session, user_id),
            },
        ).scalars().all()
        return [str(value) for value in rows]

    def list_roles(self, session: Session, company_id: UUID) -> list[RoleRecord]:
        rows = session.execute(
            text(
                """
                SELECT id, company_id, code, name, system_role, active
                FROM roles
                WHERE company_id IS NULL OR company_id = :company_id
                ORDER BY system_role DESC, code
                """
            ),
            {"company_id": _db_uuid(session, company_id)},
        ).mappings().all()
        return [self._role_from_row(row) for row in rows]

    def list_permissions(self, session: Session) -> list[str]:
        rows = session.execute(text("SELECT code FROM permissions ORDER BY code")).scalars().all()
        return [str(value) for value in rows]

    def get_assignable_role(
        self, session: Session, company_id: UUID, role_id: UUID
    ) -> RoleRecord | None:
        row = session.execute(
            text(
                """
                SELECT id, company_id, code, name, system_role, active
                FROM roles
                WHERE id = :role_id
                  AND active = true
                  AND (company_id IS NULL OR company_id = :company_id)
                """
            ),
            {
                "role_id": _db_uuid(session, role_id),
                "company_id": _db_uuid(session, company_id),
            },
        ).mappings().one_or_none()
        return self._role_from_row(row) if row is not None else None

    def replace_user_roles(
        self,
        session: Session,
        *,
        company_id: UUID,
        user_id: UUID,
        role_ids: Iterable[UUID],
        actor_user_id: UUID,
    ) -> None:
        session.execute(
            text("DELETE FROM user_roles WHERE company_id = :company_id AND user_id = :user_id"),
            {
                "company_id": _db_uuid(session, company_id),
                "user_id": _db_uuid(session, user_id),
            },
        )
        for role_id in role_ids:
            session.execute(
                text(
                    """
                    INSERT INTO user_roles (company_id, user_id, role_id, assigned_by)
                    VALUES (:company_id, :user_id, :role_id, :actor_user_id)
                    """
                ),
                {
                    "company_id": _db_uuid(session, company_id),
                    "user_id": _db_uuid(session, user_id),
                    "role_id": _db_uuid(session, role_id),
                    "actor_user_id": _db_uuid(session, actor_user_id),
                },
            )

    def create_role(
        self,
        session: Session,
        *,
        company_id: UUID,
        code: str,
        name: str,
        permission_codes: Iterable[str],
    ) -> RoleRecord:
        role_id = uuid4()
        row = session.execute(
            text(
                """
                INSERT INTO roles (id, company_id, code, name, system_role, active)
                VALUES (:id, :company_id, :code, :name, false, true)
                RETURNING id, company_id, code, name, system_role, active
                """
            ),
            {
                "id": _db_uuid(session, role_id),
                "company_id": _db_uuid(session, company_id),
                "code": code,
                "name": name,
            },
        ).mappings().one()
        role = self._role_from_row(row)
        for permission_code in permission_codes:
            inserted = session.execute(
                text(
                    """
                    INSERT INTO role_permissions (role_id, permission_id)
                    SELECT :role_id, p.id
                    FROM permissions p
                    WHERE p.code = :permission_code
                    RETURNING permission_id
                    """
                ),
                {
                    "role_id": _db_uuid(session, role.id),
                    "permission_code": permission_code,
                },
            ).scalar_one_or_none()
            if inserted is None:
                raise ValueError(f"unknown permission: {permission_code}")
        return role

    @staticmethod
    def _user_from_row(row: RowMapping) -> UserAccount:
        user_id = _uuid(row["id"])
        company_id = _uuid(row["company_id"])
        assert user_id is not None and company_id is not None
        return UserAccount(
            id=user_id,
            company_id=company_id,
            username=str(row["username"]),
            email=cast(str | None, row["email"]),
            status=str(row["status"]),
            preferred_locale=cast(str | None, row["preferred_locale"]),
            password_hash=str(row["password_hash"]),
        )

    @staticmethod
    def _role_from_row(row: RowMapping) -> RoleRecord:
        role_id = _uuid(row["id"])
        assert role_id is not None
        return RoleRecord(
            id=role_id,
            company_id=_uuid(row["company_id"]),
            code=str(row["code"]),
            name=str(row["name"]),
            system_role=bool(row["system_role"]),
            active=bool(row["active"]),
        )
