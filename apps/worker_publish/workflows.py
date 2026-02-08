"""Publish worker workflows — publishing pipeline with safety gates."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from apps.worker_publish.activities import (
        FinalizePublishInput,
        FinalizePublishOutput,
        PostToPlatformInput,
        PostToPlatformOutput,
        SafetyCheckInput,
        SafetyCheckOutput,
        finalize_publish_activity,
        post_to_platform_activity,
        safety_check_activity,
    )

TASK_QUEUE = "publish"


@dataclass
class PublishInput:
    post_id: str
    script_id: str
    platform: str
    caption: str
    risk_score: float
    risk_threshold: int
    qc_status: str
    script_text: str
    hashtags: list[str] = field(default_factory=list)
    asset_urls: dict[str, str] = field(default_factory=dict)
    utm_params: dict[str, str] = field(default_factory=dict)
    forbidden_topics: list[str] = field(default_factory=list)
    forbidden_claim_patterns: list[str] = field(default_factory=list)
    competitor_mentions: list[str] = field(default_factory=list)


@dataclass
class PublishOutput:
    post_id: str
    published: bool
    publish_status: str
    url: str | None = None
    safety_violations: list[str] = field(default_factory=list)


@workflow.defn
class PublishWorkflow:
    """Workflow: pre-publish safety check -> publish -> verify -> finalize.

    Steps:
    1. Safety gate check (risk, QC, forbidden topics, claims, competitors)
    2. Post to platform via PlatformClient
    3. Verify publication
    4. Finalize: update DB status
    """

    @workflow.run
    async def run(self, inp: PublishInput) -> PublishOutput:
        workflow.logger.info("publish_workflow_start", post_id=inp.post_id)

        retry = workflow.RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=8),
            maximum_attempts=3,
            backoff_coefficient=2.0,
        )

        # Step 1: Safety check
        safety_result: SafetyCheckOutput = await workflow.execute_activity(
            safety_check_activity,
            SafetyCheckInput(
                post_id=inp.post_id,
                script_id=inp.script_id,
                risk_score=inp.risk_score,
                risk_threshold=inp.risk_threshold,
                qc_status=inp.qc_status,
                script_text=inp.script_text,
                forbidden_topics=inp.forbidden_topics,
                forbidden_claim_patterns=inp.forbidden_claim_patterns,
                competitor_mentions=inp.competitor_mentions,
            ),
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry,
        )

        if not safety_result.passed:
            workflow.logger.warning(
                "publish_blocked_by_safety",
                post_id=inp.post_id,
                violations=safety_result.violations,
            )
            return PublishOutput(
                post_id=inp.post_id,
                published=False,
                publish_status="failed",
                safety_violations=safety_result.violations,
            )

        # Step 2: Post to platform (with retry for API errors)
        publish_retry = workflow.RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=16),
            maximum_attempts=4,
            backoff_coefficient=2.0,
        )

        platform_result: PostToPlatformOutput = await workflow.execute_activity(
            post_to_platform_activity,
            PostToPlatformInput(
                post_id=inp.post_id,
                platform=inp.platform,
                caption=inp.caption,
                hashtags=inp.hashtags,
                asset_urls=inp.asset_urls,
                utm_params=inp.utm_params,
            ),
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=publish_retry,
        )

        # Step 3: Finalize
        finalize_result: FinalizePublishOutput = await workflow.execute_activity(
            finalize_publish_activity,
            FinalizePublishInput(
                post_id=inp.post_id,
                script_id=inp.script_id,
                platform_post_id=platform_result.platform_post_id,
                post_url=platform_result.post_url,
                published=platform_result.published,
                error=platform_result.error,
            ),
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry,
        )

        workflow.logger.info(
            "publish_workflow_done",
            post_id=inp.post_id,
            status=finalize_result.publish_status,
        )

        return PublishOutput(
            post_id=inp.post_id,
            published=platform_result.published,
            publish_status=finalize_result.publish_status,
            url=finalize_result.url,
        )
