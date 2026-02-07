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
