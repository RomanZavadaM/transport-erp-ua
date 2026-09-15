from __future__ import annotations

import hmac
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import ASGIApp

from transport_erp.config import Settings
from transport_erp.identity.application.security import derive_csrf_token


class SecurityContextMiddleware(BaseHTTPMiddleware):
    _unsafe_methods = frozenset({"POST", "PUT", "PATCH", "DELETE"})
    _csrf_exempt_paths = frozenset({"/api/v1/auth/login"})

    def __init__(self, app: ASGIApp, *, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id

        if (
            request.method in self._unsafe_methods
            and request.url.path not in self._csrf_exempt_paths
        ):
            session_cookie = request.cookies.get(self.settings.session_cookie_name)
            if session_cookie is not None:
                csrf_cookie = request.cookies.get(self.settings.csrf_cookie_name)
                csrf_header = request.headers.get("X-CSRF-Token")
                expected = derive_csrf_token(session_cookie)
                if (
                    csrf_cookie is None
                    or csrf_header is None
                    or not hmac.compare_digest(csrf_cookie, expected)
                    or not hmac.compare_digest(csrf_header, expected)
                ):
                    return JSONResponse(
                        status_code=403,
                        content={
                            "error": {
                                "code": "CSRF_FAILED",
                                "message": "Request verification failed.",
                                "details": {},
                            },
                            "meta": {"request_id": request_id},
                        },
                        headers={"X-Request-ID": request_id},
                    )

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
