"""Ingest worker workflows — Temporal workflow definitions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from apps.worker_ingest.activities import (
        FetchTrendingInput,
        FetchTrendingOutput,
        StoreSourcesInput,
        StoreSourcesOutput,
        fetch_trending_activity,
        store_sources_activity,
    )

TASK_QUEUE = "ingest"


@dataclass
class TrendIngestInput:
    brand_id: str
    niches: list[str]
    platforms: list[str]
    limit_per_niche: int = 10


@dataclass
class TrendIngestOutput:
    fetched_count: int
    stored_count: int
    source_ids: list[str]


@workflow.defn
class TrendIngestWorkflow:
    """Workflow: fetch trending content and store as Sources.

    Triggered every 6 hours via schedule, or manually via API.
    """

    @workflow.run
    async def run(self, inp: TrendIngestInput) -> TrendIngestOutput:
        workflow.logger.info(
            "trend_ingest_start",
            brand_id=inp.brand_id,
            niches=inp.niches,
        )

        # Step 1: Fetch trending content from platforms
        fetch_result: FetchTrendingOutput = await workflow.execute_activity(
            fetch_trending_activity,
            FetchTrendingInput(
                brand_id=inp.brand_id,
                niches=inp.niches,
                platforms=inp.platforms,
                limit_per_niche=inp.limit_per_niche,
            ),
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=workflow.RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=30),
                maximum_attempts=3,
            ),
        )

        workflow.logger.info(
            "trend_ingest_fetched",
            count=fetch_result.items_count,
        )

        if fetch_result.items_count == 0:
            return TrendIngestOutput(
                fetched_count=0, stored_count=0, source_ids=[]
            )

        # Step 2: Store sources in database
        store_result: StoreSourcesOutput = await workflow.execute_activity(
            store_sources_activity,
            StoreSourcesInput(items=fetch_result.items),
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=workflow.RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=30),
                maximum_attempts=3,
            ),
        )

        workflow.logger.info(
            "trend_ingest_complete",
            fetched=fetch_result.items_count,
            stored=store_result.stored_count,
        )

        return TrendIngestOutput(
            fetched_count=fetch_result.items_count,
            stored_count=store_result.stored_count,
            source_ids=store_result.source_ids,
        )
