"""Instagram platform client — Graph API for Reels publishing."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from libs.platform.base import PlatformClient, PublishResult, TrendingItem

if TYPE_CHECKING:
    import httpx

logger = structlog.get_logger()

_RETRY = retry(
    retry=retry_if_exception_type((TimeoutError, ConnectionError, OSError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=15),
    reraise=True,
)

_GRAPH_BASE = "https://graph.facebook.com/v21.0"


class InstagramClient(PlatformClient):
    """Instagram platform client using the Graph API.

    Requires a Facebook/Instagram access token with:
    - `instagram_basic` — read profile/media
    - `instagram_content_publish` — publish reels
    - `pages_read_engagement` — read comments/insights

    The ig_user_id is the Instagram Business Account ID linked to the Facebook Page.
    """

    def __init__(
        self,
        access_token: str,
        ig_user_id: str,
        *,
        client: httpx.AsyncClient | None = None,
        timeout: float = 60.0,
    ) -> None:
        import httpx as _httpx

        self._token = access_token
        self._ig_user_id = ig_user_id
        self._timeout = timeout
        self._client = client or _httpx.AsyncClient(
            timeout=_httpx.Timeout(timeout),
        )

    @property
    def platform_name(self) -> str:
        return "instagram"

    def _params(self, **extra: str) -> dict[str, str]:
        return {"access_token": self._token, **extra}

    @_RETRY
    async def fetch_trending(self, niche: str, limit: int = 20) -> list[TrendingItem]:
        """Fetch recent Reels from the account's hashtag search.

        Note: Instagram doesn't have a public trending API.
        Uses hashtag search as a proxy for trending content in a niche.
        """
        logger.info("instagram_fetch_trending", niche=niche, limit=limit)

        try:
            # Step 1: Search for hashtag ID
            resp = await self._client.get(
                f"{_GRAPH_BASE}/ig_hashtag_search",
                params=self._params(q=niche, user_id=self._ig_user_id),
            )
            resp.raise_for_status()
            hashtag_data = resp.json()

            hashtags = hashtag_data.get("data", [])
            if not hashtags:
                return []

            hashtag_id = hashtags[0]["id"]

            # Step 2: Get top media for this hashtag
            media_resp = await self._client.get(
                f"{_GRAPH_BASE}/{hashtag_id}/top_media",
                params=self._params(
                    user_id=self._ig_user_id,
                    fields="id,caption,media_type,permalink,timestamp,like_count,comments_count",
                ),
            )
            media_resp.raise_for_status()
            media_data = media_resp.json()

        except Exception:
            logger.warning("instagram_trending_unavailable", niche=niche, exc_info=True)
            return []

        items: list[TrendingItem] = []
        for media in media_data.get("data", [])[:limit]:
            if media.get("media_type") not in ("VIDEO", "REELS"):
                continue
            items.append(
                TrendingItem(
                    platform="instagram",
                    url=media.get("permalink", ""),
                    author="",  # Not available via hashtag search
                    title=media.get("caption", "")[:200],
                    transcript=None,
                    features={
                        "media_type": media.get("media_type", ""),
                        "timestamp": media.get("timestamp", ""),
                    },
                    scores={
                        "likes": media.get("like_count", 0),
                        "comments": media.get("comments_count", 0),
                    },
                )
            )

        logger.info("instagram_trending_fetched", count=len(items))
        return items

    @_RETRY
    async def fetch_comments(self, url: str, limit: int = 50) -> list[dict]:
        """Fetch comments for an Instagram media item.

        The url should contain the media shortcode for lookup.
        """
        logger.info("instagram_fetch_comments", url=url, limit=limit)

        # Extract media ID — need to look up via oEmbed or known ID
        media_id = _extract_media_id(url)
        if not media_id:
            logger.warning("instagram_cannot_extract_media_id", url=url)
            return []

        try:
            resp = await self._client.get(
                f"{_GRAPH_BASE}/{media_id}/comments",
                params=self._params(fields="id,text,username,like_count,timestamp"),
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            logger.warning("instagram_comments_unavailable", url=url, exc_info=True)
            return []

        return [
            {
                "author": c.get("username", ""),
                "text": c.get("text", ""),
                "likes": c.get("like_count", 0),
                "is_question": "?" in c.get("text", ""),
            }
            for c in data.get("data", [])[:limit]
        ]

    @_RETRY
    async def publish(
        self,
        caption: str,
        hashtags: list[str],
        asset_urls: dict[str, str],
        utm_params: dict[str, str],
    ) -> PublishResult:
        """Publish a Reel to Instagram using the Graph API.

        Two-step process: create media container → publish.
        asset_urls must contain 'video' key with a publicly accessible video URL.
        """
        logger.info("instagram_publish_start", caption_len=len(caption))

        video_url = asset_urls.get("video", "")
        if not video_url:
            return PublishResult(
                post_id="", post_url="", published=False,
                error="No video URL provided",
            )

        hashtag_str = " ".join(f"#{t}" for t in hashtags)
        full_caption = f"{caption}\n\n{hashtag_str}".strip()

        try:
            # Step 1: Create media container
            container_resp = await self._client.post(
                f"{_GRAPH_BASE}/{self._ig_user_id}/media",
                params=self._params(),
                data={
                    "media_type": "REELS",
                    "video_url": video_url,
                    "caption": full_caption[:2200],
                    "share_to_feed": "true",
                },
            )
            container_resp.raise_for_status()
            container_data = container_resp.json()

            container_id = container_data.get("id", "")
            if not container_id:
                return PublishResult(
                    post_id="", post_url="", published=False,
                    error=f"Container creation failed: {container_data}",
                )

            logger.info("instagram_container_created", container_id=container_id)

            # Step 2: Wait for processing and publish
            # In production, poll /media?fields=status_code until FINISHED
            publish_resp = await self._client.post(
                f"{_GRAPH_BASE}/{self._ig_user_id}/media_publish",
                params=self._params(creation_id=container_id),
            )
            publish_resp.raise_for_status()
            publish_data = publish_resp.json()

            media_id = publish_data.get("id", "")
            post_url = f"https://www.instagram.com/reel/{media_id}/"

            return PublishResult(
                post_id=media_id,
                post_url=post_url,
                published=True,
            )

        except Exception as exc:
            logger.error("instagram_publish_failed", error=str(exc))
            return PublishResult(post_id="", post_url="", published=False, error=str(exc))

    @_RETRY
    async def verify_post(self, post_id: str) -> bool:
        """Check if a published media exists on Instagram."""
        try:
            resp = await self._client.get(
                f"{_GRAPH_BASE}/{post_id}",
                params=self._params(fields="id,media_type"),
            )
            resp.raise_for_status()
            data = resp.json()
            return bool(data.get("id"))
        except Exception:
            logger.warning("instagram_verify_failed", post_id=post_id, exc_info=True)
            return False

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()


def _extract_media_id(url: str) -> str:
    """Extract media ID from Instagram URL.

    Instagram URLs don't directly contain the numeric media ID;
    real implementation would use oEmbed or store IDs at publish time.
    Returns the shortcode as a fallback identifier.
    """
    # https://www.instagram.com/reel/ABC123/
    # https://www.instagram.com/p/ABC123/
    parts = url.rstrip("/").split("/")
    for i, part in enumerate(parts):
        if part in ("reel", "p", "tv") and i + 1 < len(parts):
            return parts[i + 1]
    return ""
