"""API key authentication for the Content Factory API.

Supports two modes:
- Single static API key (API_KEY env var) — simple deployments
- Multi-key with per-key scopes (API_KEYS env var, JSON) — production

Keys are passed via the X-API-Key header or Authorization: Bearer <key>.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from fastapi import Request

logger = structlog.get_logger()

# Paths that never require authentication
PUBLIC_PATHS: frozenset[str] = frozenset({
    "/health",
    "/health/ready",
    "/health/metrics",
    "/docs",
    "/openapi.json",
    "/redoc",
})


def _is_public_path(path: str) -> bool:
    """Check if a request path is public (no auth required)."""
    return path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc")


def _constant_time_compare(a: str, b: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks."""
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def _hash_key(key: str) -> str:
    """Create a SHA-256 hash of an API key for safe logging."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]


def generate_api_key(prefix: str = "cf") -> str:
    """Generate a cryptographically secure API key.

    Format: cf_<32 random hex chars> (e.g. cf_a1b2c3d4e5f6...)
    """
    return f"{prefix}_{secrets.token_hex(32)}"


class APIKeyAuth:
    """API key authentication handler.

    Extracts the key from X-API-Key header or Authorization: Bearer <key>.
    Validates against configured keys.
    """

    def __init__(
        self,
        *,
        api_key: str = "",
        api_keys: dict[str, list[str]] | None = None,
        enabled: bool = True,
    ) -> None:
        """Initialize auth handler.

        Args:
            api_key: Single static API key for simple deployments.
            api_keys: Multi-key map {key: [scope1, scope2, ...]} for production.
            enabled: If False, all requests are allowed (dev mode).
        """
        self._enabled = enabled
        self._single_key = api_key
        self._multi_keys = api_keys or {}

    @property
    def enabled(self) -> bool:
        return self._enabled

    def extract_key(self, request: Request) -> str | None:
        """Extract API key from request headers."""
        # Try X-API-Key header first
        key = request.headers.get("X-API-Key", "")
        if key:
            return key

        # Fall back to Authorization: Bearer <key>
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:].strip()

        return None

    def validate_key(self, key: str | None) -> tuple[bool, list[str]]:
        """Validate an API key and return (valid, scopes).

        Returns:
            Tuple of (is_valid, scopes). Scopes are ["*"] for the single-key mode.
        """
        if not self._enabled:
            return True, ["*"]

        if not key:
            return False, []

        # Check single key
        if self._single_key and _constant_time_compare(key, self._single_key):
            return True, ["*"]

        # Check multi-key map
        for stored_key, scopes in self._multi_keys.items():
            if _constant_time_compare(key, stored_key):
                return True, scopes

        return False, []

    def has_scope(self, scopes: list[str], required: str) -> bool:
        """Check if the given scopes include the required scope."""
        return "*" in scopes or required in scopes
