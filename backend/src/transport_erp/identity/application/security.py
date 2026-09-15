from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from argon2.low_level import Type


@dataclass(frozen=True, slots=True)
class ParsedSessionCookie:
    company_id: UUID
    token: str


class PasswordService:
    def __init__(self) -> None:
        self._hasher = PasswordHasher(
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            salt_len=16,
            type=Type.ID,
        )
        self._dummy_hash = self._hasher.hash("transport-erp-dummy-value")

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password_hash: str, password: str) -> bool:
        try:
            return bool(self._hasher.verify(password_hash, password))
        except (VerificationError, InvalidHashError):
            return False

    def fake_verify(self, password: str) -> None:
        self.verify(self._dummy_hash, password)

    def needs_rehash(self, password_hash: str) -> bool:
        try:
            return self._hasher.check_needs_rehash(password_hash)
        except InvalidHashError:
            return False


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def encode_session_cookie(company_id: UUID, token: str) -> str:
    return f"{company_id}.{token}"


def parse_session_cookie(value: str) -> ParsedSessionCookie:
    company_raw, separator, token = value.partition(".")
    if not separator or not token:
        raise ValueError("invalid session cookie")
    return ParsedSessionCookie(company_id=UUID(company_raw), token=token)


def derive_csrf_token(session_cookie_value: str) -> str:
    payload = f"csrf:{session_cookie_value}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
