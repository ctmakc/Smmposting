"""Ingest worker activities — individual steps executed by Temporal."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog
from temporalio import activity

from libs.db.models.source import Source
from libs.db.session import async_session
from libs.platform.factory import get_platform_client

if TYPE_CHECKING:
    from libs.platform.base import TrendingItem

logger = structlog.get_logger()


@dataclass
class FetchTrendingInput:
    brand_id: str
    niches: list[str]
    platforms: list[str]
    limit_per_niche: int = 10


@dataclass
class FetchTrendingOutput:
    items_count: int
    items: list[dict]


@activity.defn
async def fetch_trending_activity(inp: FetchTrendingInput) -> FetchTrendingOutput:
    """Fetch trending content from all configured platforms and niches."""
    logger.info(
        "fetch_trending_start",
        brand_id=inp.brand_id,
        niches=inp.niches,
        platforms=inp.platforms,
    )

    all_items: list[TrendingItem] = []
    for platform in inp.platforms:
        client = get_platform_client(platform)
        for niche in inp.niches:
            items = await client.fetch_trending(niche, limit=inp.limit_per_niche)
            all_items.extend(items)
            logger.info(
                "fetch_trending_batch",
                platform=platform,
                niche=niche,
                count=len(items),
            )

    serialized = [
        {
            "platform": item.platform,
            "url": item.url,
            "author": item.author,
            "title": item.title,
            "transcript": item.transcript,
            "features": item.features,
            "scores": item.scores,
        }
        for item in all_items
    ]

    logger.info("fetch_trending_done", total=len(serialized))
    return FetchTrendingOutput(items_count=len(serialized), items=serialized)


@dataclass
class StoreSourcesInput:
    items: list[dict]


@dataclass
class StoreSourcesOutput:
    stored_count: int
    source_ids: list[str]


@activity.defn
async def store_sources_activity(inp: StoreSourcesInput) -> StoreSourcesOutput:
    """Persist fetched trending items as Source records in the database."""
    logger.info("store_sources_start", count=len(inp.items))

    source_ids: list[str] = []
    session = await async_session()
    try:
        for item_dict in inp.items:
            source = Source(
                id=uuid.uuid4(),
                platform=item_dict["platform"],
                url=item_dict["url"],
                author=item_dict.get("author"),
                transcript=item_dict.get("transcript"),
                features=item_dict.get("features", {}),
                scores=item_dict.get("scores", {}),
            )
            session.add(source)
            source_ids.append(str(source.id))

        await session.commit()
        logger.info("store_sources_done", stored=len(source_ids))
    except Exception:
        await session.rollback()
        logger.exception("store_sources_failed")
        raise
    finally:
        await session.close()

    return StoreSourcesOutput(stored_count=len(source_ids), source_ids=source_ids)
