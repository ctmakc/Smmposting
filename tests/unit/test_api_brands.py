"""Tests for brand API endpoints with mocked repository."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apps.api.deps import get_brand_repo
from apps.api.routes.brands import router


def _make_brand(**overrides):
    """Create a fake brand-like object with attribute access."""

    class FakeBrand:
        pass

    brand = FakeBrand()
    defaults = {
        "id": uuid.uuid4(),
        "name": "TestBrand",
        "timezone": "UTC",
        "default_locale": "en",
        "niches": ["tech"],
        "platforms_enabled": ["tiktok"],
        "created_at": datetime.now(UTC),
        "updated_at": None,
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(brand, k, v)
    return brand


def _make_app(mock_repo: AsyncMock) -> FastAPI:
    app = FastAPI()
    app.include_router(router, prefix="/brands")
    app.dependency_overrides[get_brand_repo] = lambda: mock_repo
    return app


@pytest.mark.asyncio
async def test_list_brands():
    repo = AsyncMock()
    repo.list_all.return_value = [_make_brand(name="A"), _make_brand(name="B")]
    app = _make_app(repo)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/brands/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["name"] == "A"


@pytest.mark.asyncio
async def test_get_brand():
    brand_id = uuid.uuid4()
    repo = AsyncMock()
    repo.get_by_id.return_value = _make_brand(id=brand_id, name="Found")
    app = _make_app(repo)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/brands/{brand_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Found"


@pytest.mark.asyncio
async def test_get_brand_not_found():
    repo = AsyncMock()
    repo.get_by_id.return_value = None
    app = _make_app(repo)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/brands/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_brand():
    repo = AsyncMock()
    repo.create.return_value = _make_brand(name="NewBrand")
    app = _make_app(repo)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/brands/", json={"name": "NewBrand"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "NewBrand"
    repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_update_brand():
    brand_id = uuid.uuid4()
    repo = AsyncMock()
    repo.update.return_value = _make_brand(id=brand_id, name="Updated")
    app = _make_app(repo)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.patch(f"/brands/{brand_id}", json={"name": "Updated"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"


@pytest.mark.asyncio
async def test_update_brand_not_found():
    repo = AsyncMock()
    repo.update.return_value = None
    app = _make_app(repo)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.patch(f"/brands/{uuid.uuid4()}", json={"name": "X"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_brand_empty_body():
    repo = AsyncMock()
    app = _make_app(repo)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.patch(f"/brands/{uuid.uuid4()}", json={})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_delete_brand():
    repo = AsyncMock()
    repo.delete.return_value = True
    app = _make_app(repo)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.delete(f"/brands/{uuid.uuid4()}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_brand_not_found():
    repo = AsyncMock()
    repo.delete.return_value = False
    app = _make_app(repo)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.delete(f"/brands/{uuid.uuid4()}")
    assert resp.status_code == 404
