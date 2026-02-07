"""Tests for platform client abstraction and mock."""

import pytest

from libs.platform.base import PlatformClient, TrendingItem
from libs.platform.mock import MockPlatformClient


class TestTrendingItem:
    def test_defaults(self):
        item = TrendingItem(
            platform="test", url="https://example.com", author="bob", title="Hello"
        )
        assert item.platform == "test"
        assert item.transcript is None
        assert item.features == {}
        assert item.scores == {}

    def test_full(self):
        item = TrendingItem(
            platform="tiktok",
            url="https://tiktok.com/v/123",
            author="alice",
            title="Test",
            transcript="hello world",
            features={"hook_type": "question"},
            scores={"views": 1000},
        )
        assert item.transcript == "hello world"
        assert item.features["hook_type"] == "question"


class TestMockPlatformClient:
    def test_is_platform_client(self):
        client = MockPlatformClient()
        assert isinstance(client, PlatformClient)

    def test_platform_name(self):
        client = MockPlatformClient(platform="tiktok")
        assert client.platform_name == "tiktok"

    def test_default_platform_name(self):
        client = MockPlatformClient()
        assert client.platform_name == "mock"

    @pytest.mark.asyncio
    async def test_fetch_trending_returns_items(self):
        client = MockPlatformClient(platform="youtube")
        items = await client.fetch_trending("tech", limit=3)
        assert len(items) == 3
        for item in items:
            assert item.platform == "youtube"
            assert item.url.startswith("https://")
            assert item.author
            assert item.title
            assert item.transcript is not None
            assert "hook_type" in item.features
            assert "pacing" in item.features
            assert "duration" in item.features
            assert "views" in item.scores

    @pytest.mark.asyncio
    async def test_fetch_trending_unknown_niche_uses_default(self):
        client = MockPlatformClient()
        items = await client.fetch_trending("unknown_niche", limit=5)
        assert len(items) == 5

    @pytest.mark.asyncio
    async def test_fetch_trending_limit(self):
        client = MockPlatformClient()
        items = await client.fetch_trending("tech", limit=2)
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_fetch_comments(self):
        client = MockPlatformClient()
        comments = await client.fetch_comments("https://example.com/v/123", limit=5)
        assert len(comments) == 5
        for comment in comments:
            assert "author" in comment
            assert "text" in comment
            assert "likes" in comment
            assert "is_question" in comment

    @pytest.mark.asyncio
    async def test_fetch_comments_has_questions(self):
        client = MockPlatformClient()
        comments = await client.fetch_comments("https://example.com/v/123", limit=8)
        questions = [c for c in comments if c["is_question"]]
        assert len(questions) > 0
