"""Platform integration library — abstraction for social media platforms."""

from libs.platform.base import PlatformClient, TrendingItem
from libs.platform.mock import MockPlatformClient

__all__ = ["MockPlatformClient", "PlatformClient", "TrendingItem"]
