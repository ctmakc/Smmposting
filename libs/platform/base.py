"""Base platform client abstraction."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field


@dataclass
class TrendingItem:
    """A single piece of trending content from a platform."""

    platform: str
    url: str
    author: str
    title: str
    transcript: str | None = None
    features: dict = field(default_factory=dict)
    scores: dict = field(default_factory=dict)


@dataclass
class PublishResult:
    """Result of publishing content to a platform."""

    post_id: str
    post_url: str
    published: bool
    error: str | None = None


class PlatformClient(abc.ABC):
    """Abstract base class for platform integrations."""

    @property
    @abc.abstractmethod
    def platform_name(self) -> str:
        """Return the platform identifier (e.g. 'tiktok', 'youtube')."""

    @abc.abstractmethod
    async def fetch_trending(self, niche: str, limit: int = 20) -> list[TrendingItem]:
        """Fetch trending content in a given niche."""

    @abc.abstractmethod
    async def fetch_comments(self, url: str, limit: int = 50) -> list[dict]:
        """Fetch comments for a given content URL."""

    @abc.abstractmethod
    async def publish(
        self,
        caption: str,
        hashtags: list[str],
        asset_urls: dict[str, str],
        utm_params: dict[str, str],
    ) -> PublishResult:
        """Publish content to the platform."""

    @abc.abstractmethod
    async def verify_post(self, post_id: str) -> bool:
        """Verify that a published post exists on the platform."""
