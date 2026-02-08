"""Metrics worker workflows — metrics collection and learning loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from apps.worker_metrics.activities import (
        EvaluateEffectivenessInput,
        EvaluateEffectivenessOutput,
        FetchMetricsInput,
        FetchMetricsOutput,
        GenerateFollowUpInput,
        GenerateFollowUpOutput,
        StoreMetricsInput,
        UpdatePatternInput,
        UpdatePatternOutput,
        evaluate_effectiveness_activity,
        fetch_metrics_activity,
        generate_followup_ideas_activity,
        store_metrics_activity,
        update_pattern_activity,
    )

TASK_QUEUE = "metrics"

# Timer windows for metrics collection
METRICS_WINDOWS = [
    ("2h", timedelta(hours=2)),
    ("24h", timedelta(hours=24)),
    ("72h", timedelta(hours=72)),
]


@dataclass
class MetricsCollectionInput:
    post_id: str
    platform: str
    platform_post_url: str
    title: str
    brand_id: str
    brand_name: str
    niches: list[str] = field(default_factory=list)
    num_followup_ideas: int = 3


@dataclass
class MetricsCollectionOutput:
    post_id: str
    windows_collected: list[str] = field(default_factory=list)
    final_effectiveness: float = 0.0
    above_baseline: bool = False
    pattern_updated: bool = False
    followup_ideas_created: int = 0


@workflow.defn
class MetricsCollectionWorkflow:
    """Workflow: collect metrics at 2h/24h/72h, evaluate, update patterns, generate follow-ups.

    Steps per window:
    1. Wait for timer
    2. Fetch metrics from platform
    3. Store metrics in DB
    After final window (72h):
    4. Evaluate effectiveness against baseline
    5. Update pattern effectiveness score
    6. Generate follow-up ideas if above baseline
    """

    @workflow.run
    async def run(self, inp: MetricsCollectionInput) -> MetricsCollectionOutput:
        workflow.logger.info("metrics_workflow_start", post_id=inp.post_id)

        retry = workflow.RetryPolicy(
            initial_interval=timedelta(seconds=2),
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=3,
        )

        windows_collected: list[str] = []
        last_metrics: FetchMetricsOutput | None = None

        for window_name, wait_duration in METRICS_WINDOWS:
            # Step 1: Wait for timer
            workflow.logger.info(
                "metrics_waiting",
                post_id=inp.post_id,
                window=window_name,
                wait_seconds=wait_duration.total_seconds(),
            )
            await workflow.sleep(wait_duration)

            # Step 2: Fetch metrics
            fetch_result: FetchMetricsOutput = await workflow.execute_activity(
                fetch_metrics_activity,
                FetchMetricsInput(
                    post_id=inp.post_id,
                    platform=inp.platform,
                    platform_post_url=inp.platform_post_url,
                    window=window_name,
                ),
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry,
            )

            # Step 3: Store metrics
            await workflow.execute_activity(
                store_metrics_activity,
                StoreMetricsInput(
                    post_id=inp.post_id,
                    window=window_name,
                    views=fetch_result.views,
                    watch_time=fetch_result.watch_time,
                    retention=fetch_result.retention,
                    ctr=fetch_result.ctr,
                    comments=fetch_result.comments,
                    shares=fetch_result.shares,
                    saves=fetch_result.saves,
                    sentiment=fetch_result.sentiment,
                    top_questions=fetch_result.top_questions,
                ),
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=retry,
            )

            windows_collected.append(window_name)
            last_metrics = fetch_result

            workflow.logger.info(
                "metrics_collected",
                post_id=inp.post_id,
                window=window_name,
                views=fetch_result.views,
            )

        # Step 4: Evaluate effectiveness (after final 72h window)
        if last_metrics is None:
            return MetricsCollectionOutput(
                post_id=inp.post_id,
                windows_collected=windows_collected,
            )

        eval_result: EvaluateEffectivenessOutput = await workflow.execute_activity(
            evaluate_effectiveness_activity,
            EvaluateEffectivenessInput(
                post_id=inp.post_id,
                views=last_metrics.views,
                watch_time=last_metrics.watch_time,
                retention=last_metrics.retention,
                ctr=last_metrics.ctr,
                comments=last_metrics.comments,
                shares=last_metrics.shares,
                saves=last_metrics.saves,
                sentiment=last_metrics.sentiment,
            ),
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry,
        )

        workflow.logger.info(
            "effectiveness_evaluated",
            post_id=inp.post_id,
            score=eval_result.effectiveness_score,
            above_baseline=eval_result.above_baseline,
        )

        # Step 5: Update pattern effectiveness
        pattern_result: UpdatePatternOutput = await workflow.execute_activity(
            update_pattern_activity,
            UpdatePatternInput(
                post_id=inp.post_id,
                effectiveness_score=eval_result.effectiveness_score,
            ),
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry,
        )

        # Step 6: Generate follow-up ideas
        followup_result: GenerateFollowUpOutput = await workflow.execute_activity(
            generate_followup_ideas_activity,
            GenerateFollowUpInput(
                post_id=inp.post_id,
                title=inp.title,
                platform=inp.platform,
                brand_id=inp.brand_id,
                brand_name=inp.brand_name,
                niches=inp.niches,
                views=last_metrics.views,
                retention=last_metrics.retention,
                shares=last_metrics.shares,
                sentiment=last_metrics.sentiment,
                effectiveness_score=eval_result.effectiveness_score,
                above_baseline=eval_result.above_baseline,
                strongest=eval_result.strongest,
                weakest=eval_result.weakest,
                multipliers=eval_result.multipliers,
                top_questions=last_metrics.top_questions,
                num_ideas=inp.num_followup_ideas,
            ),
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry,
        )

        workflow.logger.info(
            "metrics_workflow_done",
            post_id=inp.post_id,
            effectiveness=eval_result.effectiveness_score,
            followup_ideas=followup_result.ideas_created,
        )

        return MetricsCollectionOutput(
            post_id=inp.post_id,
            windows_collected=windows_collected,
            final_effectiveness=eval_result.effectiveness_score,
            above_baseline=eval_result.above_baseline,
            pattern_updated=pattern_result.updated,
            followup_ideas_created=followup_result.ideas_created,
        )
