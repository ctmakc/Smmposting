"""Tests for API key authentication."""

from __future__ import annotations

from unittest.mock import MagicMock

from libs.auth import (
    APIKeyAuth,
    _constant_time_compare,
    _hash_key,
    _is_public_path,
    generate_api_key,
)


class TestHelpers:
    """Test auth helper functions."""

    def test_constant_time_compare_equal(self):
        assert _constant_time_compare("abc", "abc") is True

    def test_constant_time_compare_different(self):
        assert _constant_time_compare("abc", "def") is False

    def test_constant_time_compare_empty(self):
        assert _constant_time_compare("", "") is True

    def test_hash_key_returns_12_chars(self):
        result = _hash_key("some_key")
        assert len(result) == 12
        assert all(c in "0123456789abcdef" for c in result)

    def test_hash_key_deterministic(self):
        assert _hash_key("test") == _hash_key("test")

    def test_hash_key_different_keys(self):
        assert _hash_key("key1") != _hash_key("key2")

    def test_generate_api_key_format(self):
        key = generate_api_key()
        assert key.startswith("cf_")
        assert len(key) == 3 + 64  # "cf_" + 32 bytes hex

    def test_generate_api_key_unique(self):
        keys = {generate_api_key() for _ in range(10)}
        assert len(keys) == 10  # All unique

    def test_generate_api_key_custom_prefix(self):
        key = generate_api_key(prefix="test")
        assert key.startswith("test_")

    def test_is_public_path_health(self):
        assert _is_public_path("/health") is True

    def test_is_public_path_health_ready(self):
        assert _is_public_path("/health/ready") is True

    def test_is_public_path_docs(self):
        assert _is_public_path("/docs") is True

    def test_is_public_path_docs_subpath(self):
        assert _is_public_path("/docs/oauth2-redirect") is True

    def test_is_public_path_openapi(self):
        assert _is_public_path("/openapi.json") is True

    def test_is_public_path_brands_not_public(self):
        assert _is_public_path("/brands") is False

    def test_is_public_path_workflows_not_public(self):
        assert _is_public_path("/workflows") is False


class TestAPIKeyAuth:
    """Test APIKeyAuth class."""

    def test_disabled_auth_always_valid(self):
        auth = APIKeyAuth(enabled=False)
        valid, scopes = auth.validate_key(None)
        assert valid is True
        assert scopes == ["*"]

    def test_disabled_auth_property(self):
        auth = APIKeyAuth(enabled=False)
        assert auth.enabled is False

    def test_enabled_auth_no_key_invalid(self):
        auth = APIKeyAuth(api_key="secret", enabled=True)
        valid, scopes = auth.validate_key(None)
        assert valid is False
        assert scopes == []

    def test_single_key_valid(self):
        auth = APIKeyAuth(api_key="my_secret_key", enabled=True)
        valid, scopes = auth.validate_key("my_secret_key")
        assert valid is True
        assert scopes == ["*"]

    def test_single_key_invalid(self):
        auth = APIKeyAuth(api_key="my_secret_key", enabled=True)
        valid, scopes = auth.validate_key("wrong_key")
        assert valid is False
        assert scopes == []

    def test_multi_keys_valid(self):
        keys = {
            "key_admin": ["*"],
            "key_reader": ["read"],
            "key_writer": ["read", "write"],
        }
        auth = APIKeyAuth(api_keys=keys, enabled=True)

        valid, scopes = auth.validate_key("key_admin")
        assert valid is True
        assert scopes == ["*"]

        valid, scopes = auth.validate_key("key_reader")
        assert valid is True
        assert scopes == ["read"]

    def test_multi_keys_invalid(self):
        keys = {"key1": ["read"]}
        auth = APIKeyAuth(api_keys=keys, enabled=True)
        valid, scopes = auth.validate_key("bad_key")
        assert valid is False

    def test_both_single_and_multi_keys(self):
        auth = APIKeyAuth(
            api_key="master_key",
            api_keys={"other_key": ["read"]},
            enabled=True,
        )
        # Single key should work
        valid, _ = auth.validate_key("master_key")
        assert valid is True
        # Multi key should work
        valid, _ = auth.validate_key("other_key")
        assert valid is True

    def test_has_scope_wildcard(self):
        auth = APIKeyAuth()
        assert auth.has_scope(["*"], "anything") is True

    def test_has_scope_specific(self):
        auth = APIKeyAuth()
        assert auth.has_scope(["read", "write"], "read") is True

    def test_has_scope_missing(self):
        auth = APIKeyAuth()
        assert auth.has_scope(["read"], "write") is False

    def test_extract_key_x_api_key_header(self):
        auth = APIKeyAuth()
        request = MagicMock()
        request.headers = {"X-API-Key": "my_key_123"}
        assert auth.extract_key(request) == "my_key_123"

    def test_extract_key_bearer_token(self):
        auth = APIKeyAuth()
        request = MagicMock()
        request.headers = {"Authorization": "Bearer my_token_456"}
        assert auth.extract_key(request) == "my_token_456"

    def test_extract_key_prefers_x_api_key(self):
        auth = APIKeyAuth()
        request = MagicMock()
        request.headers = {
            "X-API-Key": "key_from_header",
            "Authorization": "Bearer bearer_key",
        }
        assert auth.extract_key(request) == "key_from_header"

    def test_extract_key_no_headers(self):
        auth = APIKeyAuth()
        request = MagicMock()
        request.headers = {}
        assert auth.extract_key(request) is None

    def test_extract_key_wrong_auth_scheme(self):
        auth = APIKeyAuth()
        request = MagicMock()
        request.headers = {"Authorization": "Basic dXNlcjpwYXNz"}
        assert auth.extract_key(request) is None

    def test_empty_string_key_invalid(self):
        auth = APIKeyAuth(api_key="secret", enabled=True)
        valid, _ = auth.validate_key("")
        assert valid is False
