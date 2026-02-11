"""TikTok platform client — Content Posting API integration."""

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

# TikTok API base URLs
_API_BASE = "https://open.tiktokapis.com/v2"
_RESEARCH_BASE = "https://open.tiktokapis.com/v2/research"


class TikTokClient(PlatformClient):
    """TikTok platform client using the Content Posting API.

    Requires OAuth2 access token with `video.publish` and `video.list` scopes.
    For trending data, uses the Research API (requires approved access).
    """

    def __init__(
        self,
        access_token: str,
        *,
        client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
    ) -> None:
        import httpx as _httpx

        self._token = access_token
        self._timeout = timeout
        self._client = client or _httpx.AsyncClient(
            timeout=_httpx.Timeout(timeout),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
        )

    @property
    def platform_name(self) -> str:
        return "tiktok"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    @_RETRY
    async def fetch_trending(self, niche: str, limit: int = 20) -> list[TrendingItem]:
        """Fetch trending videos via TikTok Research API.

        Requires Research API access. Falls back to empty list if unavailable.
        """
        logger.info("tiktok_fetch_trending", niche=niche, limit=limit)

        payload = {
            "query": {
                "and": [{"operation": "IN", "field_name": "keyword", "field_values": [niche]}],
            },
            "max_count": min(limit, 100),
            "start_date": "",  # API fills defaults
            "end_date": "",
        }

        try:
            resp = await self._client.post(
                f"{_RESEARCH_BASE}/video/query/",
                json=payload,
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            logger.warning("tiktok_trending_unavailable", niche=niche, exc_info=True)
            return []

        items: list[TrendingItem] = []
        for video in data.get("data", {}).get("videos", []):
            items.append(
                TrendingItem(
                    platform="tiktok",
                    url=video.get("share_url", ""),
                    author=video.get("username", ""),
                    title=video.get("video_description", ""),
                    transcript=None,
                    features={
                        "duration": video.get("duration", 0),
                        "hashtags": video.get("hashtag_names", []),
                    },
                    scores={
                        "views": video.get("view_count", 0),
                        "likes": video.get("like_count", 0),
                        "shares": video.get("share_count", 0),
                        "comments": video.get("comment_count", 0),
                    },
                )
            )
        logger.info("tiktok_trending_fetched", count=len(items))
        return items

    @_RETRY
    async def fetch_comments(self, url: str, limit: int = 50) -> list[dict]:
        """Fetch comments for a TikTok video.

        Note: Requires Research API access with `research.data.basic` scope.
        """
        logger.info("tiktok_fetch_comments", url=url, limit=limit)

        # Extract video_id from URL (format: https://www.tiktok.com/@user/video/123456)
        video_id = url.rstrip("/").split("/")[-1]

        try:
            resp = await self._client.post(
                f"{_RESEARCH_BASE}/video/comment/list/",
                json={"video_id": int(video_id), "max_count": min(limit, 100)},
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            logger.warning("tiktok_comments_unavailable", url=url, exc_info=True)
            return []

        return [
            {
                "author": c.get("username", ""),
                "text": c.get("text", ""),
                "likes": c.get("like_count", 0),
                "is_question": "?" in c.get("text", ""),
            }
            for c in data.get("data", {}).get("comments", [])
        ]

    @_RETRY
    async def publish(
        self,
        caption: str,
        hashtags: list[str],
        asset_urls: dict[str, str],
        utm_params: dict[str, str],
    ) -> PublishResult:
        """Publish a video to TikTok using the Content Posting API.

        Flow: init upload → upload video → publish.
        asset_urls must contain 'video' key with the video file URL.
        """
        logger.info("tiktok_publish_start", caption_len=len(caption))

        video_url = asset_urls.get("video", "")
        if not video_url:
            return PublishResult(
                post_id="", post_url="", published=False,
                error="No video URL provided",
            )

        hashtag_str = " ".join(f"#{t}" for t in hashtags)
        full_caption = f"{caption} {hashtag_str}".strip()

        try:
            # Step 1: Initialize upload
            init_resp = await self._client.post(
                f"{_API_BASE}/post/publish/video/init/",
                json={
                    "post_info": {
                        "title": full_caption[:150],
                        "privacy_level": "PUBLIC_TO_EVERYONE",
                        "disable_comment": False,
                        "disable_duet": False,
                        "disable_stitch": False,
                    },
                    "source_info": {
                        "source": "PULL_FROM_URL",
                        "video_url": video_url,
                    },
                },
                headers=self._headers(),
            )
            init_resp.raise_for_status()
            init_data = init_resp.json()

            publish_id = init_data.get("data", {}).get("publish_id", "")
            if not publish_id:
                return PublishResult(
                    post_id="", post_url="", published=False,
                    error=f"Init failed: {init_data}",
                )

            logger.info("tiktok_publish_initiated", publish_id=publish_id)

            # Step 2: Check status (the video is pulled and processed server-side)
            status_resp = await self._client.post(
                f"{_API_BASE}/post/publish/status/fetch/",
                json={"publish_id": publish_id},
                headers=self._headers(),
            )
            status_resp.raise_for_status()
            status_data = status_resp.json()

            upload_status = status_data.get("data", {}).get("status", "UNKNOWN")

            return PublishResult(
                post_id=publish_id,
                post_url=f"https://www.tiktok.com/@me/video/{publish_id}",
                published=upload_status in ("PUBLISH_COMPLETE", "PROCESSING"),
                error=None if upload_status != "FAILED" else f"Status: {upload_status}",
            )

        except Exception as exc:
            logger.error("tiktok_publish_failed", error=str(exc))
            return PublishResult(post_id="", post_url="", published=False, error=str(exc))

    @_RETRY
    async def verify_post(self, post_id: str) -> bool:
        """Check if a published video exists via status endpoint."""
        try:
            resp = await self._client.post(
                f"{_API_BASE}/post/publish/status/fetch/",
                json={"publish_id": post_id},
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            status = data.get("data", {}).get("status", "")
            return status == "PUBLISH_COMPLETE"
        except Exception:
            logger.warning("tiktok_verify_failed", post_id=post_id, exc_info=True)
            return False

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
