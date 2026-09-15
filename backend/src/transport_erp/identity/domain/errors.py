from __future__ import annotations


class IdentityError(Exception):
    code = "IDENTITY_ERROR"
    message = "Identity operation failed."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.message)
        self.message = message or self.message


class InvalidCredentialsError(IdentityError):
    code = "INVALID_CREDENTIALS"
    message = "Authentication failed."


class AccountUnavailableError(IdentityError):
    code = "ACCOUNT_UNAVAILABLE"
    message = "Account is unavailable."


class SessionInvalidError(IdentityError):
    code = "SESSION_INVALID"
    message = "Session is unavailable."


class IdentityNotFoundError(IdentityError):
    code = "IDENTITY_NOT_FOUND"
    message = "Identity object was not found."


class IdentityConflictError(IdentityError):
    code = "IDENTITY_CONFLICT"
    message = "Identity data conflict."
