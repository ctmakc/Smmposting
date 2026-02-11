"""Platform client factory — creates the right client based on settings."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from libs.platform.mock import MockPlatformClient

if TYPE_CHECKING:
    from libs.platform.base import PlatformClient

logger = structlog.get_logger()

# Module-level cache: platform_name → client instance
_platform_clients: dict[str, PlatformClient] = {}


def get_platform_client(
    platform: str,
    *,
    access_token: str | None = None,
    api_key: str | None = None,
    ig_user_id: str | None = None,
) -> PlatformClient:
    """Get or create a platform client for the given platform.

    Reads from Settings if no explicit args are passed.
    Supports: "tiktok", "youtube", "instagram", "mock".
    Falls back to MockPlatformClient when credentials are missing.
    """
    platform = platform.lower()

    if platform in _platform_clients:
        return _platform_clients[platform]

    # Read from config if not passed explicitly
    if access_token is None:
        from libs.core.config import get_settings

        settings = get_settings()
        if platform == "tiktok":
            access_token = settings.tiktok_access_token
        elif platform == "youtube":
            access_token = settings.youtube_access_token
            api_key = api_key or settings.youtube_api_key
        elif platform == "instagram":
            access_token = settings.instagram_access_token
            ig_user_id = ig_user_id or settings.instagram_user_id

    client: PlatformClient

    if platform == "tiktok":
        if not access_token:
            logger.warning("tiktok_token_missing, falling back to mock")
            client = MockPlatformClient(platform="tiktok")
        else:
            from libs.platform.tiktok import TikTokClient

            client = TikTokClient(access_token=access_token)

    elif platform == "youtube":
        if not access_token:
            logger.warning("youtube_token_missing, falling back to mock")
            client = MockPlatformClient(platform="youtube")
        else:
            from libs.platform.youtube import YouTubeClient

            kwargs: dict = {"access_token": access_token}
            if api_key:
                kwargs["api_key"] = api_key
            client = YouTubeClient(**kwargs)

    elif platform == "instagram":
        if not access_token or not ig_user_id:
            logger.warning("instagram_credentials_missing, falling back to mock")
            client = MockPlatformClient(platform="instagram")
        else:
            from libs.platform.instagram import InstagramClient

            client = InstagramClient(access_token=access_token, ig_user_id=ig_user_id)

    elif platform == "mock":
        client = MockPlatformClient(platform="mock")

    else:
        logger.warning("unknown_platform, falling back to mock", platform=platform)
        client = MockPlatformClient(platform=platform)

    _platform_clients[platform] = client
    logger.info("platform_client_created", platform=platform, client_type=type(client).__name__)
    return client


def reset_platform_clients() -> None:
    """Reset all cached clients (for testing)."""
    _platform_clients.clear()
