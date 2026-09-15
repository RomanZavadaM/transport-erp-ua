from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from transport_erp.identity.application.security import (
    PasswordService,
    derive_csrf_token,
    encode_session_cookie,
    generate_session_token,
    hash_session_token,
    parse_session_cookie,
)
from transport_erp.identity.domain.errors import (
    AccountUnavailableError,
    IdentityConflictError,
    IdentityNotFoundError,
    InvalidCredentialsError,
    SessionInvalidError,
)
from transport_erp.identity.domain.models import Principal, RoleRecord, SessionIssue, UserAccount
from transport_erp.identity.infrastructure.repository import IdentityRepository
from transport_erp.infrastructure.database import set_tenant_context


class IdentityService:
    def __init__(
        self,
        repository: IdentityRepository | None = None,
        passwords: PasswordService | None = None,
        session_ttl_minutes: int = 480,
    ) -> None:
        self.repository = repository or IdentityRepository()
        self.passwords = passwords or PasswordService()
        self.session_ttl_minutes = session_ttl_minutes

    def login(
        self,
        session: Session,
        *,
        company_edrpou: str,
        username: str,
        password: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> SessionIssue:
        with session.begin():
            company_id = self.repository.resolve_company_id(session, company_edrpou)
            if company_id is None:
                self.passwords.fake_verify(password)
                raise InvalidCredentialsError()

            set_tenant_context(session, company_id)
            user = self.repository.get_user_by_username(session, company_id, username)
            if user is None:
                self.passwords.fake_verify(password)
                raise InvalidCredentialsError()
            if not self.passwords.verify(user.password_hash, password):
                raise InvalidCredentialsError()
            if user.status != "ACTIVE":
                raise AccountUnavailableError()

            if self.passwords.needs_rehash(user.password_hash):
                self.repository.update_password_hash(
                    session,
                    company_id,
                    user.id,
                    self.passwords.hash(password),
                )

            issue = self._issue_session(
                session,
                user=user,
                rotated_from_id=None,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.repository.update_last_login(session, company_id, user.id)
            return issue

    def authenticate_cookie(self, session: Session, cookie_value: str) -> Principal:
        try:
            parsed = parse_session_cookie(cookie_value)
        except (ValueError, TypeError) as exc:
            raise SessionInvalidError() from exc

        with session.begin():
            set_tenant_context(session, parsed.company_id)
            result = self.repository.get_active_session_user(
                session,
                parsed.company_id,
                hash_session_token(parsed.token),
            )
            if result is None:
                raise SessionInvalidError()
            session_id, user = result
            return self._principal(session, session_id, user)

    def rotate_session(
        self,
        session: Session,
        *,
        principal: Principal,
        ip_address: str | None,
        user_agent: str | None,
    ) -> SessionIssue:
        with session.begin():
            set_tenant_context(session, principal.company_id)
            user = self.repository.get_user_by_id(session, principal.company_id, principal.user_id)
            if user is None or user.status != "ACTIVE":
                raise SessionInvalidError()
            if not self.repository.revoke_session(
                session, principal.company_id, principal.session_id
            ):
                raise SessionInvalidError()
            return self._issue_session(
                session,
                user=user,
                rotated_from_id=principal.session_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

    def logout(self, session: Session, principal: Principal) -> None:
        with session.begin():
            set_tenant_context(session, principal.company_id)
            self.repository.revoke_session(session, principal.company_id, principal.session_id)

    def list_users(self, session: Session, principal: Principal) -> list[UserAccount]:
        with session.begin():
            set_tenant_context(session, principal.company_id)
            return self.repository.list_users(session, principal.company_id)

    def get_user(self, session: Session, principal: Principal, user_id: UUID) -> UserAccount:
        with session.begin():
            set_tenant_context(session, principal.company_id)
            user = self.repository.get_user_by_id(session, principal.company_id, user_id)
            if user is None:
                raise IdentityNotFoundError()
            return user

    def create_user(
        self,
        session: Session,
        *,
        principal: Principal,
        username: str,
        email: str | None,
        password: str,
        preferred_locale: str | None,
    ) -> UserAccount:
        try:
            with session.begin():
                set_tenant_context(session, principal.company_id)
                return self.repository.create_user(
                    session,
                    company_id=principal.company_id,
                    username=username,
                    email=email,
                    password_hash=self.passwords.hash(password),
                    preferred_locale=preferred_locale,
                    actor_user_id=principal.user_id,
                )
        except IntegrityError as exc:
            raise IdentityConflictError() from exc

    def update_user_profile(
        self,
        session: Session,
        *,
        principal: Principal,
        user_id: UUID,
        email_is_set: bool,
        email: str | None,
        locale_is_set: bool,
        preferred_locale: str | None,
    ) -> UserAccount:
        try:
            with session.begin():
                set_tenant_context(session, principal.company_id)
                current = self.repository.get_user_by_id(
                    session, principal.company_id, user_id
                )
                if current is None:
                    raise IdentityNotFoundError()
                updated = self.repository.update_user_profile(
                    session,
                    company_id=principal.company_id,
                    user_id=user_id,
                    email=email if email_is_set else current.email,
                    preferred_locale=(
                        preferred_locale if locale_is_set else current.preferred_locale
                    ),
                    actor_user_id=principal.user_id,
                )
                if updated is None:
                    raise IdentityNotFoundError()
                return updated
        except IntegrityError as exc:
            raise IdentityConflictError() from exc

    def set_user_status(
        self,
        session: Session,
        *,
        principal: Principal,
        user_id: UUID,
        status: str,
    ) -> UserAccount:
        if user_id == principal.user_id and status != "ACTIVE":
            raise IdentityConflictError("Current user cannot suspend itself.")
        with session.begin():
            set_tenant_context(session, principal.company_id)
            updated = self.repository.set_user_status(
                session,
                company_id=principal.company_id,
                user_id=user_id,
                status=status,
                actor_user_id=principal.user_id,
            )
            if updated is None:
                raise IdentityNotFoundError()
            return updated

    def get_user_roles(
        self, session: Session, principal: Principal, user_id: UUID
    ) -> list[str]:
        with session.begin():
            set_tenant_context(session, principal.company_id)
            if self.repository.get_user_by_id(session, principal.company_id, user_id) is None:
                raise IdentityNotFoundError()
            return self.repository.role_codes_for_user(session, principal.company_id, user_id)

    def replace_user_roles(
        self,
        session: Session,
        *,
        principal: Principal,
        user_id: UUID,
        role_ids: list[UUID],
    ) -> list[str]:
        try:
            with session.begin():
                set_tenant_context(session, principal.company_id)
                if self.repository.get_user_by_id(
                    session, principal.company_id, user_id
                ) is None:
                    raise IdentityNotFoundError()
                for role_id in role_ids:
                    if self.repository.get_assignable_role(
                        session, principal.company_id, role_id
                    ) is None:
                        raise IdentityNotFoundError("Role is not assignable in this tenant.")
                self.repository.replace_user_roles(
                    session,
                    company_id=principal.company_id,
                    user_id=user_id,
                    role_ids=role_ids,
                    actor_user_id=principal.user_id,
                )
                return self.repository.role_codes_for_user(
                    session, principal.company_id, user_id
                )
        except IntegrityError as exc:
            raise IdentityConflictError() from exc

    def list_roles(self, session: Session, principal: Principal) -> list[RoleRecord]:
        with session.begin():
            set_tenant_context(session, principal.company_id)
            return self.repository.list_roles(session, principal.company_id)

    def list_permissions(self, session: Session, principal: Principal) -> list[str]:
        with session.begin():
            set_tenant_context(session, principal.company_id)
            return self.repository.list_permissions(session)

    def create_role(
        self,
        session: Session,
        *,
        principal: Principal,
        code: str,
        name: str,
        permission_codes: list[str],
    ) -> RoleRecord:
        try:
            with session.begin():
                set_tenant_context(session, principal.company_id)
                return self.repository.create_role(
                    session,
                    company_id=principal.company_id,
                    code=code,
                    name=name,
                    permission_codes=permission_codes,
                )
        except (IntegrityError, ValueError) as exc:
            raise IdentityConflictError(str(exc)) from exc

    def _issue_session(
        self,
        session: Session,
        *,
        user: UserAccount,
        rotated_from_id: UUID | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> SessionIssue:
        token = generate_session_token()
        expires_at = datetime.now(UTC) + timedelta(minutes=self.session_ttl_minutes)
        session_id = self.repository.create_session(
            session,
            company_id=user.company_id,
            user_id=user.id,
            token_hash=hash_session_token(token),
            expires_at=expires_at,
            rotated_from_id=rotated_from_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        principal = self._principal(session, session_id, user)
        cookie_value = encode_session_cookie(user.company_id, token)
        return SessionIssue(
            principal=principal,
            cookie_value=cookie_value,
            csrf_token=derive_csrf_token(cookie_value),
            expires_at=expires_at,
        )

    def _principal(
        self, session: Session, session_id: UUID, user: UserAccount
    ) -> Principal:
        permissions = self.repository.effective_permissions(
            session, user.company_id, user.id
        )
        return Principal(
            session_id=session_id,
            company_id=user.company_id,
            user_id=user.id,
            username=user.username,
            email=user.email,
            preferred_locale=user.preferred_locale,
            permissions=permissions,
        )
