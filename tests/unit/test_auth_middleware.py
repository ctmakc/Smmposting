"""Tests for API key authentication middleware."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from libs.auth import APIKeyAuth
from libs.auth.middleware import APIKeyMiddleware


def _make_app(*, api_key: str = "test_key", enabled: bool = True) -> FastAPI:
    """Create a test FastAPI app with auth middleware."""
    app = FastAPI()

    auth = APIKeyAuth(api_key=api_key, enabled=enabled)
    app.add_middleware(APIKeyMiddleware, auth=auth)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/brands")
    async def brands():
        return {"brands": []}

    @app.post("/workflows/trigger")
    async def trigger():
        return {"id": "123"}

    return app


class TestAuthMiddleware:
    """Test the API key middleware integration."""

    def test_public_path_no_auth_needed(self):
        app = _make_app()
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_protected_path_no_key_returns_401(self):
        app = _make_app()
        client = TestClient(app)
        resp = client.get("/brands")
        assert resp.status_code == 401
        assert "Invalid or missing API key" in resp.json()["detail"]

    def test_protected_path_wrong_key_returns_401(self):
        app = _make_app(api_key="correct_key")
        client = TestClient(app)
        resp = client.get("/brands", headers={"X-API-Key": "wrong_key"})
        assert resp.status_code == 401

    def test_protected_path_correct_key_x_api_key(self):
        app = _make_app(api_key="correct_key")
        client = TestClient(app)
        resp = client.get("/brands", headers={"X-API-Key": "correct_key"})
        assert resp.status_code == 200

    def test_protected_path_correct_key_bearer(self):
        app = _make_app(api_key="correct_key")
        client = TestClient(app)
        resp = client.get("/brands", headers={"Authorization": "Bearer correct_key"})
        assert resp.status_code == 200

    def test_auth_disabled_all_paths_allowed(self):
        app = _make_app(enabled=False)
        client = TestClient(app)
        resp = client.get("/brands")
        assert resp.status_code == 200

    def test_post_endpoint_requires_auth(self):
        app = _make_app()
        client = TestClient(app)
        resp = client.post("/workflows/trigger")
        assert resp.status_code == 401

    def test_post_endpoint_with_auth(self):
        app = _make_app(api_key="my_key")
        client = TestClient(app)
        resp = client.post(
            "/workflows/trigger", headers={"X-API-Key": "my_key"}
        )
        assert resp.status_code == 200

    def test_www_authenticate_header_on_401(self):
        app = _make_app()
        client = TestClient(app)
        resp = client.get("/brands")
        assert resp.headers.get("WWW-Authenticate") == "Bearer"

    def test_docs_path_public(self):
        app = _make_app()
        client = TestClient(app)
        # FastAPI docs redirect, but the middleware shouldn't block it
        resp = client.get("/docs")
        # Should not be 401
        assert resp.status_code != 401

    def test_openapi_json_public(self):
        app = _make_app()
        client = TestClient(app)
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
