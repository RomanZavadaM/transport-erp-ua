from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from transport_erp.identity.application.security import PasswordService


@dataclass(frozen=True, slots=True)
class LocalBootstrapResult:
    company_id: UUID
    admin_user_id: UUID
    node_id: UUID


def initialize_local_node(
    session: Session,
    *,
    company_name: str,
    legal_name: str,
    edrpou: str,
    admin_username: str,
    admin_password: str,
    node_name: str,
    passwords: PasswordService | None = None,
) -> LocalBootstrapResult:
    if session.get_bind().dialect.name != "sqlite":
        raise ValueError("Local node bootstrap is only valid for SQLite")

    password_service = passwords or PasswordService()
    company_id = uuid4()
    admin_user_id = uuid4()
    node_id = uuid4()

    with session.begin():
        company_count = session.execute(text("SELECT COUNT(*) FROM companies")).scalar_one()
        if int(company_count) != 0:
            raise RuntimeError("Local node is already initialized")

        session.execute(
            text(
                """
                INSERT INTO companies (id, name, legal_name, edrpou)
                VALUES (:id, :name, :legal_name, :edrpou)
                """
            ),
            {
                "id": str(company_id),
                "name": company_name,
                "legal_name": legal_name,
                "edrpou": edrpou,
            },
        )

        session.execute(
            text(
                """
                INSERT INTO users (
                    id, company_id, username, password_hash, preferred_locale
                )
                VALUES (:id, :company_id, :username, :password_hash, 'uk')
                """
            ),
            {
                "id": str(admin_user_id),
                "company_id": str(company_id),
                "username": admin_username,
                "password_hash": password_service.hash(admin_password),
            },
        )
        session.execute(
            text(
                """
                UPDATE users
                SET created_by = :user_id, updated_by = :user_id
                WHERE id = :user_id
                """
            ),
            {"user_id": str(admin_user_id)},
        )

        session.execute(
            text(
                """
                INSERT INTO company_settings (company_id, updated_by)
                VALUES (:company_id, :user_id)
                """
            ),
            {"company_id": str(company_id), "user_id": str(admin_user_id)},
        )

        session.execute(
            text(
                """
                INSERT INTO local_nodes (id, company_id, name, created_by)
                VALUES (:id, :company_id, :name, :created_by)
                """
            ),
            {
                "id": str(node_id),
                "company_id": str(company_id),
                "name": node_name,
                "created_by": str(admin_user_id),
            },
        )

        admin_role_id = session.execute(
            text("SELECT id FROM roles WHERE company_id IS NULL AND code = 'ADMIN'")
        ).scalar_one()
        session.execute(
            text(
                """
                INSERT INTO user_roles (company_id, user_id, role_id, assigned_by)
                VALUES (:company_id, :user_id, :role_id, :assigned_by)
                """
            ),
            {
                "company_id": str(company_id),
                "user_id": str(admin_user_id),
                "role_id": str(admin_role_id),
                "assigned_by": str(admin_user_id),
            },
        )

        session.execute(
            text(
                """
                INSERT INTO audit_log (
                    id, actor_user_id, node_id, action, entity_type, entity_id,
                    source, metadata_json
                )
                VALUES (
                    :id, :actor_user_id, :node_id, 'LOCAL_NODE_INITIALIZED',
                    'local_node', :entity_id, 'LOCAL_APP', '{}'
                )
                """
            ),
            {
                "id": str(uuid4()),
                "actor_user_id": str(admin_user_id),
                "node_id": str(node_id),
                "entity_id": str(node_id),
            },
        )

    return LocalBootstrapResult(
        company_id=company_id,
        admin_user_id=admin_user_id,
        node_id=node_id,
    )
