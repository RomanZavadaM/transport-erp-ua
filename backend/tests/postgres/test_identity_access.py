from __future__ import annotations

from typing import cast
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from psycopg import Connection
from psycopg.errors import CheckViolation

from transport_erp.identity.application.security import PasswordService
from transport_erp.main import app


def _edrpou() -> str:
    return f"{uuid4().int % 100_000_000:08d}"


def _create_company(pg: Connection[tuple[object, ...]], *, status: str = "ACTIVE") -> tuple[UUID, str]:
    edrpou = _edrpou()
    row = pg.execute(
        """
        INSERT INTO companies (name, legal_name, edrpou, status)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (f"Company {edrpou}", f"Company {edrpou}", edrpou, status),
    ).fetchone()
    assert row is not None
    return cast(UUID, row[0]), edrpou


def _create_user(
    pg: Connection[tuple[object, ...]],
    *,
    company_id: UUID,
    username: str,
    password: str,
    status: str = "ACTIVE",
    admin: bool = False,
) -> UUID:
    password_hash = PasswordService().hash(password)
    row = pg.execute(
        """
        INSERT INTO users (company_id, username, password_hash, status)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (company_id, username, password_hash, status),
    ).fetchone()
    assert row is not None
    user_id = cast(UUID, row[0])
    if admin:
        admin_row = pg.execute(
            "SELECT id FROM roles WHERE company_id IS NULL AND code = 'ADMIN'"
        ).fetchone()
        assert admin_row is not None
        pg.execute(
            """
            INSERT INTO user_roles (company_id, user_id, role_id)
            VALUES (%s, %s, %s)
            """,
            (company_id, user_id, admin_row[0]),
        )
    return user_id


def test_identity_catalog_and_admin_template_are_seeded(
    pg: Connection[tuple[object, ...]],
) -> None:
    permission_count = pg.execute("SELECT count(*) FROM permissions").fetchone()
    assert permission_count is not None
    assert int(permission_count[0]) >= 80

    admin_permissions = {
        str(row[0])
        for row in pg.execute(
            """
            SELECT p.code
            FROM roles r
            JOIN role_permissions rp ON rp.role_id = r.id
            JOIN permissions p ON p.id = rp.permission_id
            WHERE r.company_id IS NULL AND r.code = 'ADMIN'
            """
        ).fetchall()
    }
    assert "user.read" in admin_permissions
    assert "user.roles.manage" in admin_permissions
    assert "release.authorize" not in admin_permissions
    assert "medical_check.perform" not in admin_permissions


def test_auth_company_resolver_only_returns_active_company(
    pg: Connection[tuple[object, ...]],
) -> None:
    active_id, active_edrpou = _create_company(pg)
    _, suspended_edrpou = _create_company(pg, status="SUSPENDED")

    active = pg.execute("SELECT auth_resolve_company_id(%s)", (active_edrpou,)).fetchone()
    suspended = pg.execute(
        "SELECT auth_resolve_company_id(%s)", (suspended_edrpou,)
    ).fetchone()

    assert active is not None and active[0] == active_id
    assert suspended is not None and suspended[0] is None


def test_cross_tenant_role_assignment_is_rejected(
    pg: Connection[tuple[object, ...]],
) -> None:
    company_a, _ = _create_company(pg)
    company_b, _ = _create_company(pg)
    user_a = _create_user(
        pg,
        company_id=company_a,
        username=f"user-{uuid4().hex[:8]}",
        password="Correct Horse Battery Staple",
    )
    role_row = pg.execute(
        """
        INSERT INTO roles (company_id, code, name)
        VALUES (%s, %s, %s)
        RETURNING id
        """,
        (company_b, f"ROLE_{uuid4().hex[:8]}", "Other tenant role"),
    ).fetchone()
    assert role_row is not None

    with pytest.raises(CheckViolation):
        pg.execute(
            """
            INSERT INTO user_roles (company_id, user_id, role_id)
            VALUES (%s, %s, %s)
            """,
            (company_a, user_a, role_row[0]),
        )


def test_session_login_rbac_csrf_and_logout(
    pg: Connection[tuple[object, ...]],
) -> None:
    company_id, edrpou = _create_company(pg)
    username = f"admin-{uuid4().hex[:8]}"
    password = "Correct Horse Battery Staple"
    admin_id = _create_user(
        pg,
        company_id=company_id,
        username=username,
        password=password,
        admin=True,
    )

    with TestClient(app) as client:
        login = client.post(
            "/api/v1/auth/login",
            json={
                "company_edrpou": edrpou,
                "username": username,
                "password": password,
            },
        )
        assert login.status_code == 200
        assert login.json()["data"]["user"]["id"] == str(admin_id)
        assert "user.read" in login.json()["data"]["permissions"]
        assert client.cookies.get("transport_erp_session") is not None
        csrf = client.cookies.get("transport_erp_csrf")
        assert csrf is not None

        me = client.get("/api/v1/auth/me")
        assert me.status_code == 200
        users = client.get("/api/v1/users")
        assert users.status_code == 200

        no_csrf = client.post("/api/v1/auth/logout")
        assert no_csrf.status_code == 403
        assert no_csrf.json()["error"]["code"] == "CSRF_FAILED"

        logout = client.post(
            "/api/v1/auth/logout",
            headers={"X-CSRF-Token": csrf},
        )
        assert logout.status_code == 204
        after_logout = client.get("/api/v1/auth/me")
        assert after_logout.status_code == 401


def test_user_without_permission_gets_403(
    pg: Connection[tuple[object, ...]],
) -> None:
    company_id, edrpou = _create_company(pg)
    username = f"plain-{uuid4().hex[:8]}"
    password = "Correct Horse Battery Staple"
    _create_user(
        pg,
        company_id=company_id,
        username=username,
        password=password,
    )

    with TestClient(app) as client:
        login = client.post(
            "/api/v1/auth/login",
            json={
                "company_edrpou": edrpou,
                "username": username,
                "password": password,
            },
        )
        assert login.status_code == 200
        denied = client.get("/api/v1/users")
        assert denied.status_code == 403
        assert denied.json()["error"]["code"] == "PERMISSION_DENIED"


def test_suspended_user_cannot_start_session(
    pg: Connection[tuple[object, ...]],
) -> None:
    company_id, edrpou = _create_company(pg)
    username = f"suspended-{uuid4().hex[:8]}"
    password = "Correct Horse Battery Staple"
    _create_user(
        pg,
        company_id=company_id,
        username=username,
        password=password,
        status="SUSPENDED",
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "company_edrpou": edrpou,
                "username": username,
                "password": password,
            },
        )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACCOUNT_UNAVAILABLE"
