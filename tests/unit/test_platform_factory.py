"""Tests for platform client factory."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from libs.platform.factory import get_platform_client, reset_platform_clients
from libs.platform.mock import MockPlatformClient


@pytest.fixture(autouse=True)
def _reset_factory():
    """Reset factory singleton between tests."""
    reset_platform_clients()
    yield
    reset_platform_clients()


class TestGetPlatformClient:
    """Tests for get_platform_client factory."""

    def test_mock_platform(self):
        client = get_platform_client("mock")
        assert isinstance(client, MockPlatformClient)
        assert client.platform_name == "mock"

    def test_unknown_platform_returns_mock(self):
        client = get_platform_client("nonexistent")
        assert isinstance(client, MockPlatformClient)
        assert client.platform_name == "nonexistent"

    def test_singleton_caching(self):
        c1 = get_platform_client("mock")
        c2 = get_platform_client("mock")
        assert c1 is c2

    def test_different_platforms_get_different_clients(self):
        c1 = get_platform_client("mock")
        c2 = get_platform_client("unknown_other")
        assert c1 is not c2

    def test_reset_clears_cache(self):
        c1 = get_platform_client("mock")
        reset_platform_clients()
        c2 = get_platform_client("mock")
        assert c1 is not c2

    def test_tiktok_no_token_returns_mock(self):
        """Without token, TikTok should fall back to mock."""
        client = get_platform_client("tiktok", access_token="")
        assert isinstance(client, MockPlatformClient)
        assert client.platform_name == "tiktok"

    def test_tiktok_with_token_creates_real_client(self):
        """With token, should create a TikTokClient."""
        client = get_platform_client("tiktok", access_token="test_token_123")
        from libs.platform.tiktok import TikTokClient

        assert isinstance(client, TikTokClient)
        assert client.platform_name == "tiktok"

    def test_youtube_no_token_returns_mock(self):
        client = get_platform_client("youtube", access_token="")
        assert isinstance(client, MockPlatformClient)

    def test_youtube_with_token_creates_real_client(self):
        client = get_platform_client("youtube", access_token="yt_token")
        from libs.platform.youtube import YouTubeClient

        assert isinstance(client, YouTubeClient)
        assert client.platform_name == "youtube"

    def test_youtube_with_api_key(self):
        client = get_platform_client(
            "youtube", access_token="yt_token", api_key="AIza..."
        )
        from libs.platform.youtube import YouTubeClient

        assert isinstance(client, YouTubeClient)

    def test_instagram_no_token_returns_mock(self):
        client = get_platform_client("instagram", access_token="")
        assert isinstance(client, MockPlatformClient)

    def test_instagram_no_user_id_returns_mock(self):
        client = get_platform_client("instagram", access_token="ig_token", ig_user_id="")
        assert isinstance(client, MockPlatformClient)

    def test_instagram_with_credentials_creates_real_client(self):
        client = get_platform_client(
            "instagram", access_token="ig_token", ig_user_id="12345"
        )
        from libs.platform.instagram import InstagramClient

        assert isinstance(client, InstagramClient)
        assert client.platform_name == "instagram"

    def test_reads_from_settings_when_no_args(self):
        """When no explicit args, should read from Settings."""
        fake_settings = MagicMock()
        fake_settings.tiktok_access_token = "from_settings_token"

        with patch("libs.platform.factory.get_platform_client.__module__"):
            # Reset to force re-creation
            reset_platform_clients()

        with patch("libs.core.config.get_settings", return_value=fake_settings):
            client = get_platform_client("tiktok")
            from libs.platform.tiktok import TikTokClient

            assert isinstance(client, TikTokClient)

    def test_case_insensitive_platform(self):
        c1 = get_platform_client("Mock")
        assert isinstance(c1, MockPlatformClient)

    def test_case_insensitive_platform_tiktok(self):
        reset_platform_clients()
        c = get_platform_client("TikTok", access_token="tok")
        from libs.platform.tiktok import TikTokClient

        assert isinstance(c, TikTokClient)
