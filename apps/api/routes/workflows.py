"""Workflow trigger and status endpoints."""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, HTTPException
from temporalio.client import WorkflowExecutionStatus

from apps.api.schemas.workflow import (
    TriggerIngestRequest,
    TriggerIngestResponse,
    WorkflowStatusResponse,
)
from apps.worker_ingest.workflows import TASK_QUEUE, TrendIngestInput, TrendIngestWorkflow
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
        task_queue=TASK_QUEUE,
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
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}") from exc

    status_name = desc.status.name if desc.status else "UNKNOWN"

    result = None
    if desc.status == WorkflowExecutionStatus.COMPLETED:
        try:
            result_obj = await handle.result()
            result = {
                "fetched_count": result_obj.fetched_count,
                "stored_count": result_obj.stored_count,
                "source_ids": result_obj.source_ids,
            }
        except Exception:
            result = None

    return WorkflowStatusResponse(
        workflow_id=workflow_id,
        run_id=desc.run_id or "",
        status=status_name,
        result=result,
    )
