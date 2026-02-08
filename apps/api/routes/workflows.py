"""Workflow trigger and status endpoints."""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, HTTPException
from temporalio.client import WorkflowExecutionStatus

from apps.api.schemas.workflow import (
    TriggerIngestRequest,
    TriggerIngestResponse,
    TriggerMetricsRequest,
    TriggerPlanningRequest,
    TriggerPublishRequest,
    TriggerScriptRequest,
    WorkflowStatusResponse,
)
from apps.worker_analyze.workflows import TASK_QUEUE as ANALYZE_QUEUE
from apps.worker_analyze.workflows import ContentPlanningInput, ContentPlanningWorkflow
from apps.worker_generate.workflows import TASK_QUEUE as GENERATE_QUEUE
from apps.worker_generate.workflows import ScriptGenerationInput, ScriptGenerationWorkflow
from apps.worker_ingest.workflows import TASK_QUEUE as INGEST_QUEUE
from apps.worker_ingest.workflows import TrendIngestInput, TrendIngestWorkflow
from apps.worker_metrics.workflows import TASK_QUEUE as METRICS_QUEUE
from apps.worker_metrics.workflows import MetricsCollectionInput, MetricsCollectionWorkflow
from apps.worker_publish.workflows import TASK_QUEUE as PUBLISH_QUEUE
from apps.worker_publish.workflows import PublishInput, PublishWorkflow
from libs.core.temporal import get_temporal_client

logger = structlog.get_logger()

router = APIRouter()


@router.post("/ingest/trigger", response_model=TriggerIngestResponse, status_code=202)
async def trigger_ingest(body: TriggerIngestRequest) -> TriggerIngestResponse:
    """Trigger a trend ingest workflow for the given brand."""
    client = await get_temporal_client()
    workflow_id = f"ingest-{body.brand_id}-{uuid.uuid4().hex[:8]}"

    handle = await client.start_workflow(
        TrendIngestWorkflow.run,
        TrendIngestInput(
            brand_id=body.brand_id,
            niches=body.niches,
            platforms=body.platforms,
            limit_per_niche=body.limit_per_niche,
        ),
        id=workflow_id,
        task_queue=INGEST_QUEUE,
    )

    logger.info("workflow_triggered", workflow_id=workflow_id, run_id=handle.result_run_id)

    return TriggerIngestResponse(
        workflow_id=workflow_id,
        run_id=handle.result_run_id or "",
        status="started",
    )


@router.post("/planning/trigger", response_model=TriggerIngestResponse, status_code=202)
async def trigger_planning(body: TriggerPlanningRequest) -> TriggerIngestResponse:
    """Trigger a content planning workflow (gap analysis + idea generation)."""
    client = await get_temporal_client()
    workflow_id = f"planning-{body.brand_id}-{uuid.uuid4().hex[:8]}"

    handle = await client.start_workflow(
        ContentPlanningWorkflow.run,
        ContentPlanningInput(
            brand_id=body.brand_id,
            brand_name=body.brand_name,
            niches=body.niches,
            locale=body.locale,
            forbidden_topics=body.forbidden_topics,
            num_ideas=body.num_ideas,
        ),
        id=workflow_id,
        task_queue=ANALYZE_QUEUE,
    )

    logger.info("workflow_triggered", workflow_id=workflow_id, run_id=handle.result_run_id)

    return TriggerIngestResponse(
        workflow_id=workflow_id,
        run_id=handle.result_run_id or "",
        status="started",
    )


@router.post("/script/trigger", response_model=TriggerIngestResponse, status_code=202)
async def trigger_script_generation(body: TriggerScriptRequest) -> TriggerIngestResponse:
    """Trigger a script generation workflow with QC loop."""
    client = await get_temporal_client()
    workflow_id = f"script-{body.idea_id}-{uuid.uuid4().hex[:8]}"

    handle = await client.start_workflow(
        ScriptGenerationWorkflow.run,
        ScriptGenerationInput(
            idea_id=body.idea_id,
            title=body.title,
            angle=body.angle,
            persona=body.persona,
            format=body.format,
            forbidden_topics=body.forbidden_topics,
            forbidden_claims=body.forbidden_claims,
            risk_threshold=body.risk_threshold,
        ),
        id=workflow_id,
        task_queue=GENERATE_QUEUE,
    )

    logger.info("workflow_triggered", workflow_id=workflow_id, run_id=handle.result_run_id)

    return TriggerIngestResponse(
        workflow_id=workflow_id,
        run_id=handle.result_run_id or "",
        status="started",
    )


@router.post("/publish/trigger", response_model=TriggerIngestResponse, status_code=202)
async def trigger_publish(body: TriggerPublishRequest) -> TriggerIngestResponse:
    """Trigger a publish workflow for a scheduled post."""
    client = await get_temporal_client()
    workflow_id = f"publish-{body.post_id}-{uuid.uuid4().hex[:8]}"

    handle = await client.start_workflow(
        PublishWorkflow.run,
        PublishInput(
            post_id=body.post_id,
            script_id=body.script_id,
            platform=body.platform,
            caption=body.caption,
            risk_score=body.risk_score,
            risk_threshold=body.risk_threshold,
            qc_status=body.qc_status,
            script_text=body.script_text,
            hashtags=body.hashtags,
            asset_urls=body.asset_urls,
            utm_params=body.utm_params,
            forbidden_topics=body.forbidden_topics,
            forbidden_claim_patterns=body.forbidden_claim_patterns,
            competitor_mentions=body.competitor_mentions,
        ),
        id=workflow_id,
        task_queue=PUBLISH_QUEUE,
    )

    logger.info("workflow_triggered", workflow_id=workflow_id, run_id=handle.result_run_id)

    return TriggerIngestResponse(
        workflow_id=workflow_id,
        run_id=handle.result_run_id or "",
        status="started",
    )


@router.post("/metrics/trigger", response_model=TriggerIngestResponse, status_code=202)
async def trigger_metrics(body: TriggerMetricsRequest) -> TriggerIngestResponse:
    """Trigger a metrics collection workflow (2h/24h/72h timers)."""
    client = await get_temporal_client()
    workflow_id = f"metrics-{body.post_id}-{uuid.uuid4().hex[:8]}"

    handle = await client.start_workflow(
        MetricsCollectionWorkflow.run,
        MetricsCollectionInput(
            post_id=body.post_id,
            platform=body.platform,
            platform_post_url=body.platform_post_url,
            title=body.title,
            brand_id=body.brand_id,
            brand_name=body.brand_name,
            niches=body.niches,
            num_followup_ideas=body.num_followup_ideas,
        ),
        id=workflow_id,
        task_queue=METRICS_QUEUE,
    )

    logger.info("workflow_triggered", workflow_id=workflow_id, run_id=handle.result_run_id)

    return TriggerIngestResponse(
        workflow_id=workflow_id,
        run_id=handle.result_run_id or "",
        status="started",
    )


@router.get("/{workflow_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str) -> WorkflowStatusResponse:
    """Get the status of a workflow execution."""
    client = await get_temporal_client()
    handle = client.get_workflow_handle(workflow_id)

    try:
        desc = await handle.describe()
    except Exception as exc:
        raise HTTPException(
            status_code=404, detail=f"Workflow not found: {workflow_id}"
        ) from exc

    status_name = desc.status.name if desc.status else "UNKNOWN"

    result = None
    if desc.status == WorkflowExecutionStatus.COMPLETED:
        try:
            result_obj = await handle.result()
            if hasattr(result_obj, "__dataclass_fields__"):
                from dataclasses import asdict

                result = asdict(result_obj)
        except Exception:
            result = None

    return WorkflowStatusResponse(
        workflow_id=workflow_id,
        run_id=desc.run_id or "",
        status=status_name,
        result=result,
    )
