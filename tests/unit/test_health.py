"""Tests for health check endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from libs.core.middleware import _error_count, _latency_sum, _request_count


@pytest.fixture(autouse=True)
def _clear_counters():
    _request_count.clear()
    _error_count.clear()
    _latency_sum.clear()
    yield
    _request_count.clear()
    _error_count.clear()
    _latency_sum.clear()


def _make_health_app():
    """Build a minimal app with just the health router."""
    from fastapi import FastAPI

    from apps.api.routes.health import router

    app = FastAPI()
    app.include_router(router)
    return app


@pytest.mark.asyncio
async def test_liveness():
    app = _make_health_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_snapshot():
    app = _make_health_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "request_count" in data
    assert "error_count" in data
    assert "latency_sum_ms" in data
