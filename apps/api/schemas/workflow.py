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


class TriggerPlanningRequest(BaseModel):
    brand_id: str
    brand_name: str
    niches: list[str]
    locale: str = "en"
    num_ideas: int = 3
    forbidden_topics: list[str] = []


class TriggerScriptRequest(BaseModel):
    idea_id: str
    title: str
    angle: str = ""
    persona: str = ""
    format: str = "listicle"
    risk_threshold: int = 50
    forbidden_topics: list[str] = []
    forbidden_claims: list[str] = []


class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    run_id: str
    status: str
    result: dict | None = None
