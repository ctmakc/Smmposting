"""Tests for Instagram platform client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from libs.platform.instagram import InstagramClient, _extract_media_id


@pytest.fixture
def mock_httpx_client():
    client = AsyncMock()
    return client


@pytest.fixture
def ig_client(mock_httpx_client):
    return InstagramClient(
        access_token="ig_token", ig_user_id="12345", client=mock_httpx_client
    )


class TestExtractMediaId:
    """Tests for URL media ID extraction."""

    def test_reel_url(self):
        assert _extract_media_id("https://www.instagram.com/reel/ABC123/") == "ABC123"

    def test_post_url(self):
        assert _extract_media_id("https://www.instagram.com/p/XYZ789/") == "XYZ789"

    def test_tv_url(self):
        assert _extract_media_id("https://www.instagram.com/tv/DEF456/") == "DEF456"

    def test_no_match(self):
        assert _extract_media_id("https://www.instagram.com/username/") == ""

    def test_empty_string(self):
        assert _extract_media_id("") == ""


class TestInstagramClient:
    """Tests for InstagramClient."""

    def test_platform_name(self, ig_client):
        assert ig_client.platform_name == "instagram"

    @pytest.mark.asyncio
    async def test_fetch_trending_success(self, ig_client, mock_httpx_client):
        # Hashtag search response
        hashtag_resp = MagicMock()
        hashtag_resp.json.return_value = {"data": [{"id": "hashtag_123"}]}
        hashtag_resp.raise_for_status = MagicMock()

        # Media response
        media_resp = MagicMock()
        media_resp.json.return_value = {
            "data": [
                {
                    "id": "media_1",
                    "caption": "Cool reel #tech",
                    "media_type": "REELS",
                    "permalink": "https://www.instagram.com/reel/abc/",
                    "timestamp": "2025-01-01T00:00:00Z",
                    "like_count": 5000,
                    "comments_count": 200,
                },
                {
                    "id": "media_2",
                    "caption": "A photo",
                    "media_type": "IMAGE",
                    "permalink": "https://www.instagram.com/p/xyz/",
                },
            ]
        }
        media_resp.raise_for_status = MagicMock()

        mock_httpx_client.get.side_effect = [hashtag_resp, media_resp]

        items = await ig_client.fetch_trending("tech", limit=10)

        # Should only include VIDEO/REELS, not IMAGE
        assert len(items) == 1
        assert items[0].platform == "instagram"
        assert items[0].scores["likes"] == 5000

    @pytest.mark.asyncio
    async def test_fetch_trending_no_hashtags(self, ig_client, mock_httpx_client):
        resp = MagicMock()
        resp.json.return_value = {"data": []}
        resp.raise_for_status = MagicMock()
        mock_httpx_client.get.return_value = resp

        items = await ig_client.fetch_trending("obscure_niche")
        assert items == []

    @pytest.mark.asyncio
    async def test_fetch_trending_api_error(self, ig_client, mock_httpx_client):
        mock_httpx_client.get.side_effect = Exception("API error")
        items = await ig_client.fetch_trending("tech")
        assert items == []

    @pytest.mark.asyncio
    async def test_fetch_comments_success(self, ig_client, mock_httpx_client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {
                    "username": "viewer1",
                    "text": "Love this!",
                    "like_count": 5,
                    "timestamp": "2025-01-01",
                },
                {
                    "username": "viewer2",
                    "text": "What camera?",
                    "like_count": 2,
                    "timestamp": "2025-01-01",
                },
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_httpx_client.get.return_value = mock_resp

        comments = await ig_client.fetch_comments(
            "https://www.instagram.com/reel/ABC123/"
        )

        assert len(comments) == 2
        assert comments[0]["author"] == "viewer1"
        assert comments[1]["is_question"] is True

    @pytest.mark.asyncio
    async def test_fetch_comments_bad_url(self, ig_client, mock_httpx_client):
        comments = await ig_client.fetch_comments("https://example.com/nothing")
        assert comments == []

    @pytest.mark.asyncio
    async def test_fetch_comments_api_error(self, ig_client, mock_httpx_client):
        mock_httpx_client.get.side_effect = Exception("Error")
        comments = await ig_client.fetch_comments(
            "https://www.instagram.com/reel/ABC/"
        )
        assert comments == []

    @pytest.mark.asyncio
    async def test_publish_no_video_url(self, ig_client):
        result = await ig_client.publish(
            caption="Test", hashtags=[], asset_urls={}, utm_params={}
        )
        assert result.published is False
        assert "No video URL" in result.error

    @pytest.mark.asyncio
    async def test_publish_success(self, ig_client, mock_httpx_client):
        # Container creation
        container_resp = MagicMock()
        container_resp.json.return_value = {"id": "container_123"}
        container_resp.raise_for_status = MagicMock()

        # Publish response
        publish_resp = MagicMock()
        publish_resp.json.return_value = {"id": "media_456"}
        publish_resp.raise_for_status = MagicMock()

        mock_httpx_client.post.side_effect = [container_resp, publish_resp]

        result = await ig_client.publish(
            caption="My reel",
            hashtags=["test", "reels"],
            asset_urls={"video": "https://cdn.example.com/video.mp4"},
            utm_params={},
        )

        assert result.published is True
        assert result.post_id == "media_456"
        assert "instagram.com/reel" in result.post_url

    @pytest.mark.asyncio
    async def test_publish_container_fails(self, ig_client, mock_httpx_client):
        container_resp = MagicMock()
        container_resp.json.return_value = {}
        container_resp.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = container_resp

        result = await ig_client.publish(
            caption="Test",
            hashtags=[],
            asset_urls={"video": "https://cdn.example.com/v.mp4"},
            utm_params={},
        )
        assert result.published is False

    @pytest.mark.asyncio
    async def test_publish_exception(self, ig_client, mock_httpx_client):
        mock_httpx_client.post.side_effect = Exception("Network error")
        result = await ig_client.publish(
            caption="Test",
            hashtags=[],
            asset_urls={"video": "https://cdn.example.com/v.mp4"},
            utm_params={},
        )
        assert result.published is False
        assert "Network error" in result.error

    @pytest.mark.asyncio
    async def test_verify_post_success(self, ig_client, mock_httpx_client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "media_123", "media_type": "REELS"}
        mock_resp.raise_for_status = MagicMock()
        mock_httpx_client.get.return_value = mock_resp

        assert await ig_client.verify_post("media_123") is True

    @pytest.mark.asyncio
    async def test_verify_post_not_found(self, ig_client, mock_httpx_client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status = MagicMock()
        mock_httpx_client.get.return_value = mock_resp

        assert await ig_client.verify_post("bad_id") is False

    @pytest.mark.asyncio
    async def test_verify_post_error(self, ig_client, mock_httpx_client):
        mock_httpx_client.get.side_effect = Exception("Error")
        assert await ig_client.verify_post("media_123") is False
