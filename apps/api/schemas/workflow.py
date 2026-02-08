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


class TriggerPublishRequest(BaseModel):
    post_id: str
    script_id: str
    platform: str
    caption: str = ""
    risk_score: float = 0.0
    risk_threshold: int = 50
    qc_status: str = "approved"
    script_text: str = ""
    hashtags: list[str] = []
    asset_urls: dict[str, str] = {}
    utm_params: dict[str, str] = {}
    forbidden_topics: list[str] = []
    forbidden_claim_patterns: list[str] = []
    competitor_mentions: list[str] = []


class TriggerMetricsRequest(BaseModel):
    post_id: str
    platform: str
    platform_post_url: str
    title: str
    brand_id: str
    brand_name: str
    niches: list[str] = []
    num_followup_ideas: int = 3


class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    run_id: str
    status: str
    result: dict | None = None
