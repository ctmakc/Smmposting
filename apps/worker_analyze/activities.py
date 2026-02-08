"""Analyze worker activities — gap mining, idea generation, scoring."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field

import structlog
from temporalio import activity

from libs.db.enums import IdeaStatus
from libs.db.models.idea import Idea
from libs.db.session import async_session
from libs.llm.mock import MockLLMClient
from libs.llm.prompts import PromptRenderer
from libs.scoring.calculator import (
    PriorityScoreCalculator,
    PriorityScoreInput,
    RiskScoreCalculator,
    RiskScoreInput,
)

logger = structlog.get_logger()


# --- Data classes ---


@dataclass
class GapAnalysisInput:
    brand_id: str
    brand_name: str
    niches: list[str]
    locale: str
    sources: list[dict]
    questions: list[str] = field(default_factory=list)
    archive: list[dict] = field(default_factory=list)


@dataclass
class GapAnalysisOutput:
    gaps: list[dict]
    top_questions: list[str]


@dataclass
class IdeaGenerationInput:
    brand_id: str
    brand_name: str
    niches: list[str]
    locale: str
    gaps: list[dict]
    patterns: list[dict] = field(default_factory=list)
    forbidden_topics: list[str] = field(default_factory=list)
    num_ideas: int = 3


@dataclass
class IdeaGenerationOutput:
    ideas_created: int
    idea_ids: list[str]


# --- Activities ---


@activity.defn
async def analyze_gaps_activity(inp: GapAnalysisInput) -> GapAnalysisOutput:
    """Analyze content gaps using LLM."""
    logger.info("analyze_gaps_start", brand_id=inp.brand_id)

    renderer = PromptRenderer()
    prompt = renderer.render(
        "strategist/gap_analysis.j2",
        brand_name=inp.brand_name,
        niches=inp.niches,
        locale=inp.locale,
        sources=inp.sources,
        questions=inp.questions,
        archive=inp.archive,
    )

    llm = MockLLMClient()
    response = await llm.generate_structured(prompt, system="You are a content strategist.")

    result = json.loads(response.content)
    logger.info(
        "analyze_gaps_done",
        gaps_found=len(result.get("gaps", [])),
        tokens=response.total_tokens,
    )

    return GapAnalysisOutput(
        gaps=result.get("gaps", []),
        top_questions=result.get("top_questions", []),
    )


@activity.defn
async def generate_ideas_activity(inp: IdeaGenerationInput) -> IdeaGenerationOutput:
    """Generate and score content ideas, persist to DB."""
    logger.info("generate_ideas_start", brand_id=inp.brand_id, num_gaps=len(inp.gaps))

    renderer = PromptRenderer()
    prompt = renderer.render(
        "strategist/idea_generation.j2",
        brand_name=inp.brand_name,
        niches=inp.niches,
        locale=inp.locale,
        gaps=inp.gaps,
        patterns=inp.patterns,
        forbidden_topics=inp.forbidden_topics,
        num_ideas=inp.num_ideas,
    )

    llm = MockLLMClient()
    response = await llm.generate_structured(prompt, system="You are a content strategist.")
    result = json.loads(response.content)

    priority_calc = PriorityScoreCalculator()
    risk_calc = RiskScoreCalculator()
    idea_ids: list[str] = []

    session = await async_session()
    try:
        for idea_data in result.get("ideas", []):
            priority_score = priority_calc.calculate(
                PriorityScoreInput(
                    trend_score=idea_data.get("trend_score", 0),
                    gap_score=idea_data.get("gap_score", 0),
                    brand_fit=idea_data.get("brand_fit", 0),
                    effort_inverse=idea_data.get("effort_inverse", 0),
                    conversion_intent=idea_data.get("conversion_intent", 0),
                )
            )
            risk_score = risk_calc.calculate(
                RiskScoreInput(
                    claim_risk=idea_data.get("claim_risk", 0),
                    competitor_risk=idea_data.get("competitor_risk", 0),
                    policy_violation=idea_data.get("policy_violation", 0),
                    ambiguity=idea_data.get("ambiguity", 0),
                    platform_risk=idea_data.get("platform_risk", 0),
                )
            )

            idea = Idea(
                id=uuid.uuid4(),
                brand_id=uuid.UUID(inp.brand_id),
                title=idea_data["title"],
                angle=idea_data.get("angle"),
                persona=idea_data.get("persona"),
                format=idea_data.get("format"),
                priority_score=priority_score,
                risk_score=risk_score,
                effort_score=100.0 - idea_data.get("effort_inverse", 50),
                status=IdeaStatus.PLANNED,
            )
            session.add(idea)
            idea_ids.append(str(idea.id))

        await session.commit()
        logger.info("generate_ideas_done", count=len(idea_ids))
    except Exception:
        await session.rollback()
        logger.exception("generate_ideas_failed")
        raise
    finally:
        await session.close()

    return IdeaGenerationOutput(ideas_created=len(idea_ids), idea_ids=idea_ids)
