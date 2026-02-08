"""Tests for script API endpoints with mocked repository."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.api.deps import get_script_repo
from apps.api.routes.scripts import router


def _make_script(**overrides):
    class FakeScript:
        pass

    script = FakeScript()
    defaults = {
        "id": uuid.uuid4(),
        "idea_id": uuid.uuid4(),
        "version": 1,
        "hook_variants": ["Hook A", "Hook B", "Hook C"],
        "script_sections": {"intro": "Hello", "body": "Content"},
        "on_screen_text": {"title": "Title"},
        "broll_list": ["clip1.mp4"],
        "qc_status": "pending",
        "qc_notes": None,
        "generation_meta": {"model": "mock", "tokens": 100},
        "created_at": datetime.now(UTC),
        "updated_at": None,
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(script, k, v)
    return script


def _make_app(mock_repo: AsyncMock) -> FastAPI:
    app = FastAPI()
    app.include_router(router, prefix="/scripts")
    app.dependency_overrides[get_script_repo] = lambda: mock_repo
    return app


@pytest.mark.asyncio
async def test_list_scripts():
    repo = AsyncMock()
    repo.list_all.return_value = [_make_script(), _make_script()]
    app = _make_app(repo)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/scripts/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_script():
    script_id = uuid.uuid4()
    repo = AsyncMock()
    repo.get_by_id.return_value = _make_script(id=script_id)
    app = _make_app(repo)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/scripts/{script_id}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_script_not_found():
    repo = AsyncMock()
    repo.get_by_id.return_value = None
    app = _make_app(repo)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/scripts/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_approve_script():
    script_id = uuid.uuid4()
    repo = AsyncMock()
    repo.get_by_id.return_value = _make_script(id=script_id)
    repo.update.return_value = _make_script(id=script_id, qc_status="approved")
    app = _make_app(repo)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(f"/scripts/{script_id}/approve", json={})
    assert resp.status_code == 200
    assert resp.json()["qc_status"] == "approved"


@pytest.mark.asyncio
async def test_approve_script_not_found():
    repo = AsyncMock()
    repo.get_by_id.return_value = None
    app = _make_app(repo)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(f"/scripts/{uuid.uuid4()}/approve", json={})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_reject_script():
    script_id = uuid.uuid4()
    repo = AsyncMock()
    repo.get_by_id.return_value = _make_script(id=script_id)
    repo.update.return_value = _make_script(
        id=script_id, qc_status="rejected", qc_notes="Rejected: Off-brand"
    )
    app = _make_app(repo)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/scripts/{script_id}/reject", json={"reason": "Off-brand"}
        )
    assert resp.status_code == 200
    assert resp.json()["qc_status"] == "rejected"


@pytest.mark.asyncio
async def test_pending_approval_list():
    repo = AsyncMock()
    repo.get_pending_approval.return_value = [
        _make_script(qc_status="pending"),
    ]
    app = _make_app(repo)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/scripts/pending-approval/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
