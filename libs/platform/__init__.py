"""Platform integration library — abstraction for social media platforms."""

from libs.platform.base import PlatformClient, PublishResult, TrendingItem
from libs.platform.mock import MockPlatformClient

__all__ = ["MockPlatformClient", "PlatformClient", "PublishResult", "TrendingItem"]
