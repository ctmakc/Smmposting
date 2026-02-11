"""Tests for TikTok platform client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from libs.platform.tiktok import TikTokClient


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx.AsyncClient."""
    client = AsyncMock()
    return client


@pytest.fixture
def tiktok_client(mock_httpx_client):
    """Create a TikTokClient with mocked httpx."""
    return TikTokClient(access_token="test_token", client=mock_httpx_client)


class TestTikTokClient:
    """Tests for TikTokClient."""

    def test_platform_name(self, tiktok_client):
        assert tiktok_client.platform_name == "tiktok"

    @pytest.mark.asyncio
    async def test_fetch_trending_success(self, tiktok_client, mock_httpx_client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "videos": [
                    {
                        "share_url": "https://tiktok.com/@user/video/123",
                        "username": "creator1",
                        "video_description": "Amazing trend",
                        "duration": 30,
                        "hashtag_names": ["tech", "ai"],
                        "view_count": 1000000,
                        "like_count": 50000,
                        "share_count": 5000,
                        "comment_count": 2000,
                    },
                    {
                        "share_url": "https://tiktok.com/@user2/video/456",
                        "username": "creator2",
                        "video_description": "Another trend",
                        "duration": 60,
                        "hashtag_names": ["coding"],
                        "view_count": 500000,
                        "like_count": 25000,
                        "share_count": 2500,
                        "comment_count": 1000,
                    },
                ]
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_resp

        items = await tiktok_client.fetch_trending("tech", limit=5)

        assert len(items) == 2
        assert items[0].platform == "tiktok"
        assert items[0].author == "creator1"
        assert items[0].title == "Amazing trend"
        assert items[0].scores["views"] == 1000000
        assert items[0].features["duration"] == 30

    @pytest.mark.asyncio
    async def test_fetch_trending_api_error_returns_empty(self, tiktok_client, mock_httpx_client):
        mock_httpx_client.post.side_effect = Exception("API unavailable")

        items = await tiktok_client.fetch_trending("tech")
        assert items == []

    @pytest.mark.asyncio
    async def test_fetch_comments_success(self, tiktok_client, mock_httpx_client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {
                "comments": [
                    {"username": "user1", "text": "Great video!", "like_count": 10},
                    {"username": "user2", "text": "How did you do this?", "like_count": 5},
                ]
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_resp

        comments = await tiktok_client.fetch_comments(
            "https://www.tiktok.com/@user/video/123456"
        )

        assert len(comments) == 2
        assert comments[0]["author"] == "user1"
        assert comments[1]["is_question"] is True

    @pytest.mark.asyncio
    async def test_fetch_comments_error_returns_empty(self, tiktok_client, mock_httpx_client):
        mock_httpx_client.post.side_effect = Exception("Error")
        comments = await tiktok_client.fetch_comments("https://tiktok.com/@u/video/123")
        assert comments == []

    @pytest.mark.asyncio
    async def test_publish_no_video_url(self, tiktok_client):
        result = await tiktok_client.publish(
            caption="Test", hashtags=["test"], asset_urls={}, utm_params={}
        )
        assert result.published is False
        assert "No video URL" in result.error

    @pytest.mark.asyncio
    async def test_publish_success(self, tiktok_client, mock_httpx_client):
        # Mock init response
        init_resp = MagicMock()
        init_resp.json.return_value = {"data": {"publish_id": "pub_123"}}
        init_resp.raise_for_status = MagicMock()

        # Mock status response
        status_resp = MagicMock()
        status_resp.json.return_value = {"data": {"status": "PUBLISH_COMPLETE"}}
        status_resp.raise_for_status = MagicMock()

        mock_httpx_client.post.side_effect = [init_resp, status_resp]

        result = await tiktok_client.publish(
            caption="My video",
            hashtags=["test"],
            asset_urls={"video": "https://cdn.example.com/video.mp4"},
            utm_params={},
        )

        assert result.published is True
        assert result.post_id == "pub_123"
        assert "tiktok.com" in result.post_url

    @pytest.mark.asyncio
    async def test_publish_init_fails(self, tiktok_client, mock_httpx_client):
        init_resp = MagicMock()
        init_resp.json.return_value = {"data": {}}
        init_resp.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = init_resp

        result = await tiktok_client.publish(
            caption="Test",
            hashtags=[],
            asset_urls={"video": "https://cdn.example.com/v.mp4"},
            utm_params={},
        )
        assert result.published is False

    @pytest.mark.asyncio
    async def test_publish_exception(self, tiktok_client, mock_httpx_client):
        mock_httpx_client.post.side_effect = Exception("Network error")

        result = await tiktok_client.publish(
            caption="Test",
            hashtags=[],
            asset_urls={"video": "https://cdn.example.com/v.mp4"},
            utm_params={},
        )
        assert result.published is False
        assert "Network error" in result.error

    @pytest.mark.asyncio
    async def test_verify_post_success(self, tiktok_client, mock_httpx_client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {"status": "PUBLISH_COMPLETE"}}
        mock_resp.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_resp

        assert await tiktok_client.verify_post("pub_123") is True

    @pytest.mark.asyncio
    async def test_verify_post_not_complete(self, tiktok_client, mock_httpx_client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": {"status": "PROCESSING"}}
        mock_resp.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_resp

        assert await tiktok_client.verify_post("pub_123") is False

    @pytest.mark.asyncio
    async def test_verify_post_error(self, tiktok_client, mock_httpx_client):
        mock_httpx_client.post.side_effect = Exception("Error")
        assert await tiktok_client.verify_post("pub_123") is False
