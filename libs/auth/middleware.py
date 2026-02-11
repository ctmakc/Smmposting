"""Auth middleware — API key validation for FastAPI."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from starlette.middleware.base import BaseHTTPMiddleware

from libs.auth import APIKeyAuth, _is_public_path

if TYPE_CHECKING:
    from fastapi import Request, Response
    from starlette.middleware.base import RequestResponseEndpoint

logger = structlog.get_logger()


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces API key authentication on non-public paths."""

    def __init__(self, app: object, auth: APIKeyAuth) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._auth = auth

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip auth for public paths
        if _is_public_path(request.url.path):
            return await call_next(request)

        # Skip if auth is disabled (dev mode)
        if not self._auth.enabled:
            return await call_next(request)

        # Extract and validate key
        key = self._auth.extract_key(request)
        valid, scopes = self._auth.validate_key(key)

        if not valid:
            logger.warning(
                "auth_failed",
                path=request.url.path,
                method=request.method,
                reason="invalid_or_missing_key",
            )
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Store scopes on request state for downstream use
        request.state.auth_scopes = scopes

        return await call_next(request)
