from uuid import uuid4

from transport_erp.identity.application.security import (
    PasswordService,
    derive_csrf_token,
    encode_session_cookie,
    hash_session_token,
    parse_session_cookie,
)


def test_password_service_uses_argon2id_and_verifies() -> None:
    passwords = PasswordService()
    password_hash = passwords.hash("Correct Horse Battery Staple")

    assert password_hash.startswith("$argon2id$")
    assert passwords.verify(password_hash, "Correct Horse Battery Staple") is True
    assert passwords.verify(password_hash, "wrong-value") is False


def test_session_cookie_roundtrip_and_csrf_binding() -> None:
    company_id = uuid4()
    token = "opaque-session-token"
    cookie = encode_session_cookie(company_id, token)
    parsed = parse_session_cookie(cookie)

    assert parsed.company_id == company_id
    assert parsed.token == token
    assert len(hash_session_token(token)) == 64
    assert derive_csrf_token(cookie) == derive_csrf_token(cookie)
    assert derive_csrf_token(cookie) != derive_csrf_token(
        encode_session_cookie(company_id, "another-token")
    )
