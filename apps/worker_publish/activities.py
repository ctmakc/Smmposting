"""Publish worker activities — safety check, publish, verify."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

import structlog
from temporalio import activity

from libs.db.enums import IdeaStatus, PublishStatus
from libs.db.session import async_session
from libs.platform.mock import MockPlatformClient
from libs.publishing.safety import SafetyGate

logger = structlog.get_logger()


# --- Activity I/O dataclasses ---


@dataclass
class SafetyCheckInput:
    post_id: str
    script_id: str
    risk_score: float
    risk_threshold: int
    qc_status: str
    script_text: str
    forbidden_topics: list[str] = field(default_factory=list)
    forbidden_claim_patterns: list[str] = field(default_factory=list)
    competitor_mentions: list[str] = field(default_factory=list)


@dataclass
class SafetyCheckOutput:
    passed: bool
    violations: list[str] = field(default_factory=list)


@dataclass
class PostToPlatformInput:
    post_id: str
    platform: str
    caption: str
    hashtags: list[str] = field(default_factory=list)
    asset_urls: dict[str, str] = field(default_factory=dict)
    utm_params: dict[str, str] = field(default_factory=dict)


@dataclass
class PostToPlatformOutput:
    platform_post_id: str
    post_url: str
    published: bool
    error: str | None = None


@dataclass
class FinalizePublishInput:
    post_id: str
    script_id: str
    platform_post_id: str
    post_url: str
    published: bool
    error: str | None = None


@dataclass
class FinalizePublishOutput:
    post_id: str
    publish_status: str
    url: str | None = None


# --- Activities ---


@activity.defn
async def safety_check_activity(inp: SafetyCheckInput) -> SafetyCheckOutput:
    """Run pre-publish safety gate checks."""
    logger.info("safety_check_start", post_id=inp.post_id)

    gate = SafetyGate()
    result = gate.check(
        risk_score=inp.risk_score,
        risk_threshold=inp.risk_threshold,
        qc_status=inp.qc_status,
        script_text=inp.script_text,
        forbidden_topics=inp.forbidden_topics,
        forbidden_claim_patterns=inp.forbidden_claim_patterns,
        competitor_mentions=inp.competitor_mentions,
    )

    if not result.passed:
        logger.warning(
            "safety_check_failed",
            post_id=inp.post_id,
            violations=result.violations,
        )
        # Mark post as FAILED in DB
        async with async_session() as session:
            from libs.db.repositories.post import PostRepository

            repo = PostRepository(session)
            await repo.update(
                uuid.UUID(inp.post_id),
                publish_status=PublishStatus.FAILED,
            )
            await session.commit()

    return SafetyCheckOutput(passed=result.passed, violations=result.violations)


@activity.defn
async def post_to_platform_activity(inp: PostToPlatformInput) -> PostToPlatformOutput:
    """Publish content to the target platform."""
    logger.info("post_to_platform_start", post_id=inp.post_id, platform=inp.platform)

    # Update status to PUBLISHING
    async with async_session() as session:
        from libs.db.repositories.post import PostRepository

        repo = PostRepository(session)
        await repo.update(uuid.UUID(inp.post_id), publish_status=PublishStatus.PUBLISHING)
        await session.commit()

    # Use mock client for now — will be swapped for real clients per platform
    client = MockPlatformClient(platform=inp.platform)

    result = await client.publish(
        caption=inp.caption,
        hashtags=inp.hashtags,
        asset_urls=inp.asset_urls,
        utm_params=inp.utm_params,
    )

    if not result.published:
        logger.error("post_to_platform_failed", post_id=inp.post_id, error=result.error)
        return PostToPlatformOutput(
            platform_post_id="",
            post_url="",
            published=False,
            error=result.error,
        )

    # Verify post exists on platform
    verified = await client.verify_post(result.post_id)
    if not verified:
        logger.warning("post_verification_failed", post_id=inp.post_id)

    return PostToPlatformOutput(
        platform_post_id=result.post_id,
        post_url=result.post_url,
        published=result.published,
    )


@activity.defn
async def finalize_publish_activity(inp: FinalizePublishInput) -> FinalizePublishOutput:
    """Update DB records after publish attempt."""
    logger.info("finalize_publish", post_id=inp.post_id, published=inp.published)

    async with async_session() as session:
        from datetime import UTC, datetime

        from sqlalchemy import select

        from libs.db.models.idea import Idea
        from libs.db.models.post import Post
        from libs.db.models.script import Script
        from libs.db.repositories.post import PostRepository

        post_repo = PostRepository(session)

        post_uuid = uuid.UUID(inp.post_id)

        if inp.published:
            # Update post
            await post_repo.update(
                post_uuid,
                publish_status=PublishStatus.PUBLISHED,
                url=inp.post_url,
                published_at=datetime.now(UTC),
            )

            # Update idea status to PUBLISHED
            post_row = await session.execute(
                select(Post).where(Post.id == post_uuid)
            )
            post = post_row.scalar_one_or_none()
            if post:
                script_row = await session.execute(
                    select(Script).where(Script.id == post.script_id)
                )
                script = script_row.scalar_one_or_none()
                if script:
                    idea_row = await session.execute(
                        select(Idea).where(Idea.id == script.idea_id)
                    )
                    idea = idea_row.scalar_one_or_none()
                    if idea:
                        idea.status = IdeaStatus.PUBLISHED

            status = PublishStatus.PUBLISHED.value
        else:
            await post_repo.update(
                post_uuid,
                publish_status=PublishStatus.FAILED,
            )
            status = PublishStatus.FAILED.value

        await session.commit()

    return FinalizePublishOutput(
        post_id=inp.post_id,
        publish_status=status,
        url=inp.post_url if inp.published else None,
    )
