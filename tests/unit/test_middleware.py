"""Tests for request logging, error handling middleware, and in-process metrics."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from libs.core.middleware import (
    ErrorHandlerMiddleware,
    RequestLoggingMiddleware,
    _error_count,
    _latency_sum,
    _request_count,
    get_metrics_snapshot,
    setup_middleware,
)


@pytest.fixture(autouse=True)
def _clear_counters():
    """Reset in-process counters before each test."""
    _request_count.clear()
    _error_count.clear()
    _latency_sum.clear()
    yield
    _request_count.clear()
    _error_count.clear()
    _latency_sum.clear()


def _make_app(*, raise_exc: bool = False) -> FastAPI:
    app = FastAPI()

    @app.get("/ok")
    async def ok_route():
        return {"status": "ok"}

    @app.get("/fail")
    async def fail_route():
        if raise_exc:
            raise RuntimeError("boom")
        return {"status": "fail"}

    @app.get("/not-found")
    async def not_found_route():
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=404, content={"detail": "not found"})

    setup_middleware(app)
    return app


@pytest.mark.asyncio
async def test_request_logging_increments_counter():
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/ok")
    assert resp.status_code == 200
    snapshot = get_metrics_snapshot()
    assert snapshot["request_count"]["GET /ok"] == 1
    assert "GET /ok" in snapshot["latency_sum_ms"]


@pytest.mark.asyncio
async def test_multiple_requests_accumulate():
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/ok")
        await client.get("/ok")
        await client.get("/ok")
    snapshot = get_metrics_snapshot()
    assert snapshot["request_count"]["GET /ok"] == 3


@pytest.mark.asyncio
async def test_error_handler_returns_500():
    app = _make_app(raise_exc=True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/fail")
    assert resp.status_code == 500
    assert resp.json() == {"detail": "Internal server error"}


@pytest.mark.asyncio
async def test_4xx_does_not_increment_error_count():
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/not-found")
    snapshot = get_metrics_snapshot()
    assert snapshot["error_count"].get("GET /not-found", 0) == 0


@pytest.mark.asyncio
async def test_metrics_snapshot_structure():
    snapshot = get_metrics_snapshot()
    assert "request_count" in snapshot
    assert "error_count" in snapshot
    assert "latency_sum_ms" in snapshot


class TestSetupMiddleware:
    def test_adds_middleware_to_app(self):
        app = FastAPI()
        setup_middleware(app)
        middleware_classes = [m.cls for m in app.user_middleware]
        assert ErrorHandlerMiddleware in middleware_classes
        assert RequestLoggingMiddleware in middleware_classes
