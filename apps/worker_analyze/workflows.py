"""Analyze worker workflows — gap mining and content planning."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from apps.worker_analyze.activities import (
        GapAnalysisInput,
        GapAnalysisOutput,
        IdeaGenerationInput,
        IdeaGenerationOutput,
        analyze_gaps_activity,
        generate_ideas_activity,
    )

TASK_QUEUE = "analyze"


@dataclass
class ContentPlanningInput:
    brand_id: str
    brand_name: str
    niches: list[str]
    locale: str
    sources: list[dict] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
    archive: list[dict] = field(default_factory=list)
    patterns: list[dict] = field(default_factory=list)
    forbidden_topics: list[str] = field(default_factory=list)
    num_ideas: int = 3


@dataclass
class ContentPlanningOutput:
    gaps_found: int
    ideas_created: int
    idea_ids: list[str]
    top_questions: list[str]


@workflow.defn
class ContentPlanningWorkflow:
    """Workflow: analyze gaps and generate content ideas.

    Triggered daily or manually via API.
    """

    @workflow.run
    async def run(self, inp: ContentPlanningInput) -> ContentPlanningOutput:
        workflow.logger.info("content_planning_start", brand_id=inp.brand_id)

        retry = workflow.RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=3,
        )

        # Step 1: Analyze gaps
        gap_result: GapAnalysisOutput = await workflow.execute_activity(
            analyze_gaps_activity,
            GapAnalysisInput(
                brand_id=inp.brand_id,
                brand_name=inp.brand_name,
                niches=inp.niches,
                locale=inp.locale,
                sources=inp.sources,
                questions=inp.questions,
                archive=inp.archive,
            ),
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry,
        )

        workflow.logger.info("gaps_analyzed", count=len(gap_result.gaps))

        if not gap_result.gaps:
            return ContentPlanningOutput(
                gaps_found=0, ideas_created=0, idea_ids=[], top_questions=[]
            )

        # Step 2: Generate ideas from gaps
        idea_result: IdeaGenerationOutput = await workflow.execute_activity(
            generate_ideas_activity,
            IdeaGenerationInput(
                brand_id=inp.brand_id,
                brand_name=inp.brand_name,
                niches=inp.niches,
                locale=inp.locale,
                gaps=gap_result.gaps,
                patterns=inp.patterns,
                forbidden_topics=inp.forbidden_topics,
                num_ideas=inp.num_ideas,
            ),
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry,
        )

        workflow.logger.info(
            "content_planning_complete",
            gaps=len(gap_result.gaps),
            ideas=idea_result.ideas_created,
        )

        return ContentPlanningOutput(
            gaps_found=len(gap_result.gaps),
            ideas_created=idea_result.ideas_created,
            idea_ids=idea_result.idea_ids,
            top_questions=gap_result.top_questions,
        )
