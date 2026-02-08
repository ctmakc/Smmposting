"""Tests for platform client publish functionality."""

import pytest

from libs.platform.mock import MockPlatformClient


class TestMockPlatformPublish:
    @pytest.fixture()
    def client(self):
        return MockPlatformClient(platform="tiktok")

    @pytest.mark.asyncio
    async def test_publish_returns_result(self, client):
        result = await client.publish(
            caption="Test caption #trending",
            hashtags=["#trending", "#viral"],
            asset_urls={"video": "s3://bucket/video.mp4"},
            utm_params={"source": "content_factory"},
        )
        assert result.published is True
        assert result.post_id != ""
        assert "tiktok.example.com" in result.post_url
        assert result.error is None

    @pytest.mark.asyncio
    async def test_verify_post(self, client):
        verified = await client.verify_post("some_post_id")
        assert verified is True

    @pytest.mark.asyncio
    async def test_publish_different_platforms(self):
        for platform in ("tiktok", "youtube", "instagram"):
            client = MockPlatformClient(platform=platform)
            result = await client.publish(
                caption="Test",
                hashtags=[],
                asset_urls={},
                utm_params={},
            )
            assert result.published is True
            assert platform in result.post_url
