"""Metrics worker activities — fetch, store, evaluate, learn."""

from __future__ import annotations

import json
import random
import uuid
from dataclasses import dataclass, field

import structlog
from temporalio import activity

from libs.db.enums import IdeaStatus, MetricsWindow
from libs.db.session import async_session
from libs.llm.mock import MockLLMClient
from libs.llm.prompts import PromptRenderer
from libs.platform.mock import MockPlatformClient
from libs.scoring.effectiveness import (
    BaselineMetrics,
    EffectivenessScorer,
    MetricsSnapshot,
)

logger = structlog.get_logger()


# --- Activity I/O dataclasses ---


@dataclass
class FetchMetricsInput:
    post_id: str
    platform: str
    platform_post_url: str
    window: str  # "2h", "24h", "72h"


@dataclass
class FetchMetricsOutput:
    post_id: str
    window: str
    views: int = 0
    watch_time: float = 0.0
    retention: float = 0.0
    ctr: float = 0.0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    sentiment: float = 0.0
    top_questions: list[str] = field(default_factory=list)


@dataclass
class StoreMetricsInput:
    post_id: str
    window: str
    views: int = 0
    watch_time: float = 0.0
    retention: float = 0.0
    ctr: float = 0.0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    sentiment: float = 0.0
    top_questions: list[str] = field(default_factory=list)


@dataclass
class StoreMetricsOutput:
    metrics_id: str


@dataclass
class EvaluateEffectivenessInput:
    post_id: str
    views: int = 0
    watch_time: float = 0.0
    retention: float = 0.0
    ctr: float = 0.0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    sentiment: float = 0.0


@dataclass
class EvaluateEffectivenessOutput:
    effectiveness_score: float
    above_baseline: bool
    strongest: str
    weakest: str
    multipliers: dict[str, float] = field(default_factory=dict)


@dataclass
class UpdatePatternInput:
    post_id: str
    effectiveness_score: float


@dataclass
class UpdatePatternOutput:
    pattern_id: str | None
    updated: bool


@dataclass
class GenerateFollowUpInput:
    post_id: str
    title: str
    platform: str
    brand_id: str
    brand_name: str
    niches: list[str]
    views: int
    retention: float
    shares: int
    sentiment: float
    effectiveness_score: float
    above_baseline: bool
    strongest: str
    weakest: str
    multipliers: dict[str, float] = field(default_factory=dict)
    top_questions: list[str] = field(default_factory=list)
    num_ideas: int = 3


@dataclass
class GenerateFollowUpOutput:
    ideas_created: int
    idea_ids: list[str] = field(default_factory=list)


# --- Activities ---


@activity.defn
async def fetch_metrics_activity(inp: FetchMetricsInput) -> FetchMetricsOutput:
    """Fetch performance metrics from the platform."""
    logger.info("fetch_metrics_start", post_id=inp.post_id, window=inp.window)

    # Mock metrics — in production would call platform API
    client = MockPlatformClient(platform=inp.platform)
    comments_data = await client.fetch_comments(inp.platform_post_url, limit=20)

    window_multipliers = {"2h": 1.0, "24h": 3.0, "72h": 5.0}
    mult = window_multipliers.get(inp.window, 1.0)

    questions = [c["text"] for c in comments_data if c.get("is_question")]

    return FetchMetricsOutput(
        post_id=inp.post_id,
        window=inp.window,
        views=int(random.randint(500, 50000) * mult),
        watch_time=round(random.uniform(10.0, 60.0) * mult, 1),
        retention=round(random.uniform(20.0, 80.0), 1),
        ctr=round(random.uniform(1.0, 10.0), 2),
        comments=int(random.randint(5, 200) * mult),
        shares=int(random.randint(2, 100) * mult),
        saves=int(random.randint(1, 50) * mult),
        sentiment=round(random.uniform(-0.3, 0.8), 2),
        top_questions=questions[:5],
    )


@activity.defn
async def store_metrics_activity(inp: StoreMetricsInput) -> StoreMetricsOutput:
    """Store collected metrics in DB."""
    logger.info("store_metrics", post_id=inp.post_id, window=inp.window)

    async with async_session() as session:
        from libs.db.repositories.metrics import MetricsRepository

        repo = MetricsRepository(session)
        window_enum = MetricsWindow(inp.window)

        metrics = await repo.create(
            post_id=uuid.UUID(inp.post_id),
            window=window_enum,
            views=inp.views,
            watch_time=inp.watch_time,
            retention=inp.retention,
            ctr=inp.ctr,
            comments=inp.comments,
            shares=inp.shares,
            saves=inp.saves,
            sentiment=inp.sentiment,
            top_questions=inp.top_questions,
        )
        await session.commit()

    return StoreMetricsOutput(metrics_id=str(metrics.id))


@activity.defn
async def evaluate_effectiveness_activity(
    inp: EvaluateEffectivenessInput,
) -> EvaluateEffectivenessOutput:
    """Compare metrics against baseline and compute effectiveness score."""
    logger.info("evaluate_effectiveness", post_id=inp.post_id)

    # In production, baseline would come from DB aggregation per brand/format
    baseline = BaselineMetrics(
        avg_views=10000.0,
        avg_watch_time=30.0,
        avg_retention=45.0,
        avg_ctr=4.0,
        avg_comments=50.0,
        avg_shares=20.0,
        avg_saves=10.0,
        avg_sentiment=0.3,
    )

    snapshot = MetricsSnapshot(
        views=inp.views,
        watch_time=inp.watch_time,
        retention=inp.retention,
        ctr=inp.ctr,
        comments=inp.comments,
        shares=inp.shares,
        saves=inp.saves,
        sentiment=inp.sentiment,
    )

    scorer = EffectivenessScorer()
    result = scorer.evaluate(snapshot, baseline)

    return EvaluateEffectivenessOutput(
        effectiveness_score=result.score,
        above_baseline=result.above_baseline,
        strongest=result.strongest,
        weakest=result.weakest,
        multipliers=result.multipliers,
    )


@activity.defn
async def update_pattern_activity(inp: UpdatePatternInput) -> UpdatePatternOutput:
    """Update the pattern's effectiveness score based on post performance."""
    logger.info("update_pattern", post_id=inp.post_id)

    async with async_session() as session:
        from sqlalchemy import select

        from libs.db.models.idea import Idea
        from libs.db.models.pattern import Pattern
        from libs.db.models.post import Post
        from libs.db.models.script import Script

        # Navigate: post -> script -> idea -> pattern
        post_uuid = uuid.UUID(inp.post_id)
        post = (await session.execute(
            select(Post).where(Post.id == post_uuid)
        )).scalar_one_or_none()

        if not post:
            return UpdatePatternOutput(pattern_id=None, updated=False)

        script = (await session.execute(
            select(Script).where(Script.id == post.script_id)
        )).scalar_one_or_none()

        if not script:
            return UpdatePatternOutput(pattern_id=None, updated=False)

        idea = (await session.execute(
            select(Idea).where(Idea.id == script.idea_id)
        )).scalar_one_or_none()

        if not idea or not idea.pattern_id:
            return UpdatePatternOutput(pattern_id=None, updated=False)

        pattern = (await session.execute(
            select(Pattern).where(Pattern.id == idea.pattern_id)
        )).scalar_one_or_none()

        if not pattern:
            return UpdatePatternOutput(pattern_id=None, updated=False)

        # Exponential moving average: new = 0.3 * current + 0.7 * old
        pattern.effectiveness_score = round(
            0.3 * inp.effectiveness_score + 0.7 * pattern.effectiveness_score, 1
        )

        # Update idea status to LEARNING
        idea.status = IdeaStatus.LEARNING

        await session.commit()

    return UpdatePatternOutput(
        pattern_id=str(pattern.id),
        updated=True,
    )


@activity.defn
async def generate_followup_ideas_activity(
    inp: GenerateFollowUpInput,
) -> GenerateFollowUpOutput:
    """Generate follow-up ideas based on post performance using LLM."""
    logger.info(
        "generate_followup_ideas",
        post_id=inp.post_id,
        above_baseline=inp.above_baseline,
    )

    renderer = PromptRenderer()
    prompt = renderer.render(
        "strategist/followup_ideas.j2",
        title=inp.title,
        platform=inp.platform,
        views=inp.views,
        views_multiplier=inp.multipliers.get("views", 1.0),
        retention=inp.retention,
        retention_multiplier=inp.multipliers.get("retention", 1.0),
        shares=inp.shares,
        shares_multiplier=inp.multipliers.get("shares", 1.0),
        sentiment=inp.sentiment,
        sentiment_multiplier=inp.multipliers.get("sentiment", 1.0),
        effectiveness_score=inp.effectiveness_score,
        strongest=inp.strongest,
        weakest=inp.weakest,
        top_questions=inp.top_questions,
        brand_name=inp.brand_name,
        niches=inp.niches,
        above_baseline=inp.above_baseline,
        num_ideas=inp.num_ideas,
    )

    llm = MockLLMClient()
    response = await llm.generate(prompt)

    try:
        parsed = json.loads(response.content)
        ideas_data = parsed.get("ideas", [])
    except (json.JSONDecodeError, AttributeError):
        ideas_data = []

    idea_ids: list[str] = []

    if ideas_data:
        async with async_session() as session:
            from libs.db.repositories.idea import IdeaRepository

            repo = IdeaRepository(session)
            for idea_data in ideas_data[:inp.num_ideas]:
                idea = await repo.create(
                    brand_id=uuid.UUID(inp.brand_id),
                    title=idea_data.get("title", "Follow-up idea"),
                    angle=idea_data.get("angle", ""),
                    format=idea_data.get("format", "listicle"),
                    status=IdeaStatus.BACKLOG,
                    priority_score=60.0,  # boosted follow-up
                    risk_score=20.0,
                )
                idea_ids.append(str(idea.id))
            await session.commit()

    return GenerateFollowUpOutput(
        ideas_created=len(idea_ids),
        idea_ids=idea_ids,
    )
