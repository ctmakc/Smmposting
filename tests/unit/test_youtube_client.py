"""Tests for YouTube platform client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from libs.platform.youtube import YouTubeClient, _extract_video_id


@pytest.fixture
def mock_httpx_client():
    client = AsyncMock()
    return client


@pytest.fixture
def yt_client(mock_httpx_client):
    return YouTubeClient(
        access_token="yt_token", api_key="AIza_test", client=mock_httpx_client
    )


class TestExtractVideoId:
    """Tests for URL video ID extraction."""

    def test_shorts_url(self):
        assert _extract_video_id("https://www.youtube.com/shorts/abc123") == "abc123"

    def test_shorts_url_with_params(self):
        assert _extract_video_id("https://www.youtube.com/shorts/abc123?si=xyz") == "abc123"

    def test_watch_url(self):
        assert _extract_video_id("https://www.youtube.com/watch?v=abc123") == "abc123"

    def test_watch_url_with_extra_params(self):
        assert _extract_video_id("https://www.youtube.com/watch?v=abc123&t=10") == "abc123"

    def test_youtu_be_url(self):
        assert _extract_video_id("https://youtu.be/abc123") == "abc123"

    def test_raw_id(self):
        assert _extract_video_id("abc123") == "abc123"


class TestYouTubeClient:
    """Tests for YouTubeClient."""

    def test_platform_name(self, yt_client):
        assert yt_client.platform_name == "youtube"

    @pytest.mark.asyncio
    async def test_fetch_trending_success(self, yt_client, mock_httpx_client):
        # Search response
        search_resp = MagicMock()
        search_resp.json.return_value = {
            "items": [
                {
                    "id": {"videoId": "vid1"},
                    "snippet": {
                        "title": "Cool Short",
                        "channelTitle": "Creator",
                        "channelId": "UC123",
                        "publishedAt": "2025-01-01T00:00:00Z",
                    },
                }
            ]
        }
        search_resp.raise_for_status = MagicMock()

        # Stats response
        stats_resp = MagicMock()
        stats_resp.json.return_value = {
            "items": [
                {
                    "id": "vid1",
                    "statistics": {
                        "viewCount": "100000",
                        "likeCount": "5000",
                        "commentCount": "200",
                    },
                }
            ]
        }
        stats_resp.raise_for_status = MagicMock()

        mock_httpx_client.get.side_effect = [search_resp, stats_resp]

        items = await yt_client.fetch_trending("tech", limit=5)

        assert len(items) == 1
        assert items[0].platform == "youtube"
        assert items[0].title == "Cool Short"
        assert items[0].scores["views"] == 100000
        assert "shorts" in items[0].url

    @pytest.mark.asyncio
    async def test_fetch_trending_api_error(self, yt_client, mock_httpx_client):
        mock_httpx_client.get.side_effect = Exception("API error")
        items = await yt_client.fetch_trending("tech")
        assert items == []

    @pytest.mark.asyncio
    async def test_fetch_comments_success(self, yt_client, mock_httpx_client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "items": [
                {
                    "snippet": {
                        "topLevelComment": {
                            "snippet": {
                                "authorDisplayName": "Viewer",
                                "textOriginal": "How did you do this?",
                                "likeCount": 15,
                            }
                        }
                    }
                }
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_httpx_client.get.return_value = mock_resp

        comments = await yt_client.fetch_comments(
            "https://www.youtube.com/shorts/abc123"
        )

        assert len(comments) == 1
        assert comments[0]["author"] == "Viewer"
        assert comments[0]["is_question"] is True

    @pytest.mark.asyncio
    async def test_fetch_comments_error(self, yt_client, mock_httpx_client):
        mock_httpx_client.get.side_effect = Exception("Error")
        comments = await yt_client.fetch_comments("https://youtube.com/shorts/x")
        assert comments == []

    @pytest.mark.asyncio
    async def test_publish_no_video_url(self, yt_client):
        result = await yt_client.publish(
            caption="Test", hashtags=[], asset_urls={}, utm_params={}
        )
        assert result.published is False
        assert "No video URL" in result.error

    @pytest.mark.asyncio
    async def test_verify_post_success(self, yt_client, mock_httpx_client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "items": [{"id": "vid1", "status": {"uploadStatus": "processed"}}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_httpx_client.get.return_value = mock_resp

        assert await yt_client.verify_post("vid1") is True

    @pytest.mark.asyncio
    async def test_verify_post_not_processed(self, yt_client, mock_httpx_client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "items": [{"id": "vid1", "status": {"uploadStatus": "uploading"}}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_httpx_client.get.return_value = mock_resp

        assert await yt_client.verify_post("vid1") is False

    @pytest.mark.asyncio
    async def test_verify_post_empty_items(self, yt_client, mock_httpx_client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"items": []}
        mock_resp.raise_for_status = MagicMock()
        mock_httpx_client.get.return_value = mock_resp

        assert await yt_client.verify_post("vid1") is False

    @pytest.mark.asyncio
    async def test_verify_post_error(self, yt_client, mock_httpx_client):
        mock_httpx_client.get.side_effect = Exception("Error")
        assert await yt_client.verify_post("vid1") is False
