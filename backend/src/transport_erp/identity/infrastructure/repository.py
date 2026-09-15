from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from transport_erp.identity.domain.models import RoleRecord, UserAccount


class IdentityRepository:
    def resolve_company_id(self, session: Session, edrpou: str) -> UUID | None:
        value = session.execute(
            text("SELECT auth_resolve_company_id(:edrpou)"),
            {"edrpou": edrpou},
        ).scalar_one_or_none()
        return cast(UUID | None, value)

    def get_user_by_username(
        self, session: Session, company_id: UUID, username: str
    ) -> UserAccount | None:
        row = session.execute(
            text(
                """
                SELECT id, company_id, username::text AS username, email::text AS email,
                       status, preferred_locale, password_hash
                FROM users
                WHERE company_id = :company_id AND username = :username
                """
            ),
            {"company_id": company_id, "username": username},
        ).mappings().one_or_none()
        return self._user_from_row(row) if row is not None else None

    def get_user_by_id(
        self, session: Session, company_id: UUID, user_id: UUID
    ) -> UserAccount | None:
        row = session.execute(
            text(
                """
                SELECT id, company_id, username::text AS username, email::text AS email,
                       status, preferred_locale, password_hash
                FROM users
                WHERE company_id = :company_id AND id = :user_id
                """
            ),
            {"company_id": company_id, "user_id": user_id},
        ).mappings().one_or_none()
        return self._user_from_row(row) if row is not None else None

    def get_active_session_user(
        self, session: Session, company_id: UUID, token_hash: str
    ) -> tuple[UUID, UserAccount] | None:
        row = session.execute(
            text(
                """
                SELECT s.id AS session_id,
                       u.id, u.company_id, u.username::text AS username,
                       u.email::text AS email, u.status, u.preferred_locale, u.password_hash
                FROM user_sessions s
                JOIN users u
                  ON u.company_id = s.company_id AND u.id = s.user_id
                JOIN companies c ON c.id = s.company_id
                WHERE s.company_id = :company_id
                  AND s.token_hash = :token_hash
                  AND s.revoked_at IS NULL
                  AND s.expires_at > now()
                  AND u.status = 'ACTIVE'
                  AND c.status = 'ACTIVE'
                """
            ),
            {"company_id": company_id, "token_hash": token_hash},
        ).mappings().one_or_none()
        if row is None:
            return None
        return cast(UUID, row["session_id"]), self._user_from_row(row)

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
            {"company_id": company_id, "user_id": user_id},
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
        value = session.execute(
            text(
                """
                INSERT INTO user_sessions (
                    company_id, user_id, token_hash, expires_at,
                    rotated_from_id, ip_address, user_agent
                )
                VALUES (
                    :company_id, :user_id, :token_hash, :expires_at,
                    :rotated_from_id, CAST(:ip_address AS inet), :user_agent
                )
                RETURNING id
                """
            ),
            {
                "company_id": company_id,
                "user_id": user_id,
                "token_hash": token_hash,
                "expires_at": expires_at,
                "rotated_from_id": rotated_from_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
            },
        ).scalar_one()
        return cast(UUID, value)

    def revoke_session(self, session: Session, company_id: UUID, session_id: UUID) -> bool:
        value = session.execute(
            text(
                """
                UPDATE user_sessions
                SET revoked_at = now()
                WHERE company_id = :company_id
                  AND id = :session_id
                  AND revoked_at IS NULL
                RETURNING id
                """
            ),
            {"company_id": company_id, "session_id": session_id},
        ).scalar_one_or_none()
        return value is not None

    def update_last_login(self, session: Session, company_id: UUID, user_id: UUID) -> None:
        session.execute(
            text(
                """
                UPDATE users
                SET last_login_at = now(), updated_at = now(), row_version = row_version + 1
                WHERE company_id = :company_id AND id = :user_id
                """
            ),
            {"company_id": company_id, "user_id": user_id},
        )

    def update_password_hash(
        self, session: Session, company_id: UUID, user_id: UUID, password_hash: str
    ) -> None:
        session.execute(
            text(
                """
                UPDATE users
                SET password_hash = :password_hash,
                    updated_at = now(), row_version = row_version + 1
                WHERE company_id = :company_id AND id = :user_id
                """
            ),
            {"company_id": company_id, "user_id": user_id, "password_hash": password_hash},
        )

    def list_users(self, session: Session, company_id: UUID) -> list[UserAccount]:
        rows = session.execute(
            text(
                """
                SELECT id, company_id, username::text AS username, email::text AS email,
                       status, preferred_locale, password_hash
                FROM users
                WHERE company_id = :company_id
                ORDER BY username
                """
            ),
            {"company_id": company_id},
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
        row = session.execute(
            text(
                """
                INSERT INTO users (
                    company_id, username, email, password_hash, preferred_locale,
                    created_by, updated_by
                )
                VALUES (
                    :company_id, :username, :email, :password_hash, :preferred_locale,
                    :actor_user_id, :actor_user_id
                )
                RETURNING id, company_id, username::text AS username, email::text AS email,
                          status, preferred_locale, password_hash
                """
            ),
            {
                "company_id": company_id,
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "preferred_locale": preferred_locale,
                "actor_user_id": actor_user_id,
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
                    updated_at = now(), updated_by = :actor_user_id,
                    row_version = row_version + 1
                WHERE company_id = :company_id AND id = :user_id
                RETURNING id, company_id, username::text AS username, email::text AS email,
                          status, preferred_locale, password_hash
                """
            ),
            {
                "company_id": company_id,
                "user_id": user_id,
                "email": email,
                "preferred_locale": preferred_locale,
                "actor_user_id": actor_user_id,
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
                    updated_at = now(), updated_by = :actor_user_id,
                    row_version = row_version + 1
                WHERE company_id = :company_id AND id = :user_id
                RETURNING id, company_id, username::text AS username, email::text AS email,
                          status, preferred_locale, password_hash
                """
            ),
            {
                "company_id": company_id,
                "user_id": user_id,
                "status": status,
                "actor_user_id": actor_user_id,
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
            {"company_id": company_id, "user_id": user_id},
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
            {"company_id": company_id},
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
            {"role_id": role_id, "company_id": company_id},
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
            {"company_id": company_id, "user_id": user_id},
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
                    "company_id": company_id,
                    "user_id": user_id,
                    "role_id": role_id,
                    "actor_user_id": actor_user_id,
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
        row = session.execute(
            text(
                """
                INSERT INTO roles (company_id, code, name, system_role, active)
                VALUES (:company_id, :code, :name, false, true)
                RETURNING id, company_id, code, name, system_role, active
                """
            ),
            {"company_id": company_id, "code": code, "name": name},
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
                {"role_id": role.id, "permission_code": permission_code},
            ).scalar_one_or_none()
            if inserted is None:
                raise ValueError(f"unknown permission: {permission_code}")
        return role

    @staticmethod
    def _user_from_row(row: RowMapping) -> UserAccount:
        return UserAccount(
            id=cast(UUID, row["id"]),
            company_id=cast(UUID, row["company_id"]),
            username=str(row["username"]),
            email=cast(str | None, row["email"]),
            status=str(row["status"]),
            preferred_locale=cast(str | None, row["preferred_locale"]),
            password_hash=str(row["password_hash"]),
        )

    @staticmethod
    def _role_from_row(row: RowMapping) -> RoleRecord:
        return RoleRecord(
            id=cast(UUID, row["id"]),
            company_id=cast(UUID | None, row["company_id"]),
            code=str(row["code"]),
            name=str(row["name"]),
            system_role=bool(row["system_role"]),
            active=bool(row["active"]),
        )
