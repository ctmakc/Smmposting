"""Workflow API schemas."""

from __future__ import annotations

from pydantic import BaseModel


class TriggerIngestRequest(BaseModel):
    brand_id: str
    niches: list[str]
    platforms: list[str]
    limit_per_niche: int = 10


class TriggerIngestResponse(BaseModel):
    workflow_id: str
    run_id: str
    status: str = "started"


class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    run_id: str
    status: str
    result: dict | None = None
