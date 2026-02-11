"""YouTube platform client — Data API v3 + Resumable Upload for Shorts."""

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

_API_BASE = "https://www.googleapis.com/youtube/v3"
_UPLOAD_BASE = "https://www.googleapis.com/upload/youtube/v3"


class YouTubeClient(PlatformClient):
    """YouTube platform client for Shorts via Data API v3.

    Requires OAuth2 access token with `youtube.upload` and `youtube.readonly` scopes.
    Videos under 60s with vertical aspect ratio are auto-classified as Shorts.
    """

    def __init__(
        self,
        access_token: str,
        *,
        api_key: str = "",
        client: httpx.AsyncClient | None = None,
        timeout: float = 60.0,
    ) -> None:
        import httpx as _httpx

        self._token = access_token
        self._api_key = api_key
        self._timeout = timeout
        self._client = client or _httpx.AsyncClient(
            timeout=_httpx.Timeout(timeout),
            headers={"Authorization": f"Bearer {access_token}"},
        )

    @property
    def platform_name(self) -> str:
        return "youtube"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    @_RETRY
    async def fetch_trending(self, niche: str, limit: int = 20) -> list[TrendingItem]:
        """Fetch trending/popular Shorts via YouTube Data API search."""
        logger.info("youtube_fetch_trending", niche=niche, limit=limit)

        params: dict[str, str | int] = {
            "part": "snippet",
            "q": f"{niche} #shorts",
            "type": "video",
            "videoDuration": "short",
            "order": "viewCount",
            "maxResults": min(limit, 50),
        }
        if self._api_key:
            params["key"] = self._api_key

        try:
            resp = await self._client.get(
                f"{_API_BASE}/search",
                params=params,
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            logger.warning("youtube_trending_unavailable", niche=niche, exc_info=True)
            return []

        # Get video statistics in bulk
        video_ids = [
            item["id"]["videoId"]
            for item in data.get("items", [])
            if item.get("id", {}).get("videoId")
        ]

        stats_map: dict[str, dict] = {}
        if video_ids:
            stats_map = await self._fetch_video_stats(video_ids)

        items: list[TrendingItem] = []
        for item in data.get("items", []):
            vid_id = item.get("id", {}).get("videoId", "")
            snippet = item.get("snippet", {})
            stats = stats_map.get(vid_id, {})

            items.append(
                TrendingItem(
                    platform="youtube",
                    url=f"https://www.youtube.com/shorts/{vid_id}",
                    author=snippet.get("channelTitle", ""),
                    title=snippet.get("title", ""),
                    transcript=None,
                    features={
                        "channel_id": snippet.get("channelId", ""),
                        "published_at": snippet.get("publishedAt", ""),
                    },
                    scores={
                        "views": int(stats.get("viewCount", 0)),
                        "likes": int(stats.get("likeCount", 0)),
                        "comments": int(stats.get("commentCount", 0)),
                    },
                )
            )

        logger.info("youtube_trending_fetched", count=len(items))
        return items

    async def _fetch_video_stats(self, video_ids: list[str]) -> dict[str, dict]:
        """Bulk fetch video statistics."""
        try:
            params: dict[str, str] = {
                "part": "statistics",
                "id": ",".join(video_ids[:50]),
            }
            if self._api_key:
                params["key"] = self._api_key

            resp = await self._client.get(
                f"{_API_BASE}/videos",
                params=params,
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                item["id"]: item.get("statistics", {})
                for item in data.get("items", [])
            }
        except Exception:
            logger.warning("youtube_stats_unavailable", exc_info=True)
            return {}

    @_RETRY
    async def fetch_comments(self, url: str, limit: int = 50) -> list[dict]:
        """Fetch comments for a YouTube video."""
        logger.info("youtube_fetch_comments", url=url, limit=limit)

        # Extract video_id from URL (supports /watch?v=X, /shorts/X)
        video_id = _extract_video_id(url)

        try:
            params: dict[str, str | int] = {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": min(limit, 100),
                "order": "relevance",
            }
            if self._api_key:
                params["key"] = self._api_key

            resp = await self._client.get(
                f"{_API_BASE}/commentThreads",
                params=params,
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            logger.warning("youtube_comments_unavailable", url=url, exc_info=True)
            return []

        return [
            {
                "author": c["snippet"]["topLevelComment"]["snippet"].get("authorDisplayName", ""),
                "text": (
                    c["snippet"]["topLevelComment"]["snippet"].get("textOriginal", "")
                ),
                "likes": c["snippet"]["topLevelComment"]["snippet"].get("likeCount", 0),
                "is_question": "?" in c["snippet"]["topLevelComment"]["snippet"].get(
                    "textOriginal", ""
                ),
            }
            for c in data.get("items", [])
            if c.get("snippet", {}).get("topLevelComment")
        ]

    @_RETRY
    async def publish(
        self,
        caption: str,
        hashtags: list[str],
        asset_urls: dict[str, str],
        utm_params: dict[str, str],
    ) -> PublishResult:
        """Upload a Short to YouTube via resumable upload API.

        asset_urls must contain 'video' key with the video file URL.
        The video must be <=60s and vertical for Shorts classification.
        """
        logger.info("youtube_publish_start", caption_len=len(caption))

        video_url = asset_urls.get("video", "")
        if not video_url:
            return PublishResult(
                post_id="", post_url="", published=False,
                error="No video URL provided",
            )

        hashtag_str = " ".join(f"#{t}" for t in hashtags)
        title = f"{caption[:90]} {hashtag_str}".strip()[:100]
        description = f"{caption}\n\n{hashtag_str}".strip()

        try:
            # Step 1: Initialize resumable upload
            metadata = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "categoryId": "22",  # People & Blogs
                    "tags": hashtags[:30],
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False,
                    "shorts": {"shortsEligible": True},
                },
            }

            init_resp = await self._client.post(
                f"{_UPLOAD_BASE}/videos?uploadType=resumable&part=snippet,status",
                json=metadata,
                headers={
                    **self._headers(),
                    "Content-Type": "application/json",
                    "X-Upload-Content-Type": "video/*",
                },
            )
            init_resp.raise_for_status()

            upload_url = init_resp.headers.get("Location", "")
            if not upload_url:
                return PublishResult(
                    post_id="", post_url="", published=False,
                    error="No upload URL in response",
                )

            # Step 2: Download video from asset URL and upload to YouTube
            import httpx as _httpx

            async with _httpx.AsyncClient(timeout=_httpx.Timeout(120.0)) as dl_client:
                video_resp = await dl_client.get(video_url)
                video_resp.raise_for_status()
                video_bytes = video_resp.content

            upload_resp = await self._client.put(
                upload_url,
                content=video_bytes,
                headers={
                    **self._headers(),
                    "Content-Type": "video/*",
                    "Content-Length": str(len(video_bytes)),
                },
            )
            upload_resp.raise_for_status()
            upload_data = upload_resp.json()

            video_id = upload_data.get("id", "")
            return PublishResult(
                post_id=video_id,
                post_url=f"https://www.youtube.com/shorts/{video_id}",
                published=True,
            )

        except Exception as exc:
            logger.error("youtube_publish_failed", error=str(exc))
            return PublishResult(post_id="", post_url="", published=False, error=str(exc))

    @_RETRY
    async def verify_post(self, post_id: str) -> bool:
        """Check if a published video exists via Videos.list."""
        try:
            params: dict[str, str] = {"part": "status", "id": post_id}
            if self._api_key:
                params["key"] = self._api_key

            resp = await self._client.get(
                f"{_API_BASE}/videos",
                params=params,
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            return len(items) > 0 and items[0].get("status", {}).get("uploadStatus") == "processed"
        except Exception:
            logger.warning("youtube_verify_failed", post_id=post_id, exc_info=True)
            return False

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()


def _extract_video_id(url: str) -> str:
    """Extract video ID from various YouTube URL formats."""
    # https://www.youtube.com/shorts/VIDEO_ID
    if "/shorts/" in url:
        return url.split("/shorts/")[1].split("?")[0].split("/")[0]
    # https://www.youtube.com/watch?v=VIDEO_ID
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    # https://youtu.be/VIDEO_ID
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return url
