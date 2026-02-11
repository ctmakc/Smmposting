"""FastAPI middleware — request logging, error handling, metrics."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import structlog
from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from fastapi import FastAPI, Request, Response
    from starlette.middleware.base import RequestResponseEndpoint

logger = structlog.get_logger()

# --- In-process Prometheus-style counters (no external dep needed) ---

_request_count: dict[str, int] = {}
_error_count: dict[str, int] = {}
_latency_sum: dict[str, float] = {}


def get_metrics_snapshot() -> dict:
    """Return current metrics for /health/metrics endpoint."""
    return {
        "request_count": dict(_request_count),
        "error_count": dict(_error_count),
        "latency_sum_ms": {k: round(v, 2) for k, v in _latency_sum.items()},
    }


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every request with method, path, status, and latency."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.monotonic()
        method = request.method
        path = request.url.path

        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.monotonic() - start) * 1000
            logger.error(
                "request_error",
                method=method,
                path=path,
                elapsed_ms=round(elapsed_ms, 2),
                exc_info=True,
            )
            key = f"{method} {path}"
            _error_count[key] = _error_count.get(key, 0) + 1
            raise

        elapsed_ms = (time.monotonic() - start) * 1000
        status = response.status_code
        key = f"{method} {path}"

        _request_count[key] = _request_count.get(key, 0) + 1
        _latency_sum[key] = _latency_sum.get(key, 0.0) + elapsed_ms

        if status >= 500:
            _error_count[key] = _error_count.get(key, 0) + 1

        log_level = "warning" if status >= 400 else "info"
        getattr(logger, log_level)(
            "request",
            method=method,
            path=path,
            status=status,
            elapsed_ms=round(elapsed_ms, 2),
        )

        return response


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Catches unhandled exceptions and returns 500 with structured error."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except Exception:
            logger.error(
                "unhandled_error",
                method=request.method,
                path=request.url.path,
                exc_info=True,
            )
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )


def setup_middleware(app: FastAPI) -> None:
    """Add all middleware to the FastAPI app (order matters — outer first)."""
    import json

    from libs.auth import APIKeyAuth
    from libs.auth.middleware import APIKeyMiddleware
    from libs.core.config import get_settings

    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # API key auth (outermost — runs last in middleware stack)
    settings = get_settings()
    multi_keys: dict[str, list[str]] = {}
    if settings.api_keys_json:
        try:
            multi_keys = json.loads(settings.api_keys_json)
        except json.JSONDecodeError:
            logger.error("invalid_api_keys_json, auth will use single key only")

    auth = APIKeyAuth(
        api_key=settings.api_key,
        api_keys=multi_keys,
        enabled=settings.auth_enabled,
    )
    app.add_middleware(APIKeyMiddleware, auth=auth)
