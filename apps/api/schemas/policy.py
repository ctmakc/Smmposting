"""Policy API schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PolicyCreate(BaseModel):
    brand_id: uuid.UUID
    forbidden_topics: list[str] = []
    forbidden_claim_patterns: list[str] = []
    competitor_rules: dict[str, Any] = {}
    risk_threshold_auto_publish: int = Field(default=50, ge=0, le=100)
    vocabulary: dict[str, Any] = {}


class PolicyUpdate(BaseModel):
    forbidden_topics: list[str] | None = None
    forbidden_claim_patterns: list[str] | None = None
    competitor_rules: dict[str, Any] | None = None
    risk_threshold_auto_publish: int | None = Field(default=None, ge=0, le=100)
    vocabulary: dict[str, Any] | None = None


class PolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    forbidden_topics: list[str]
    forbidden_claim_patterns: list[str]
    competitor_rules: dict[str, Any]
    risk_threshold_auto_publish: int
    vocabulary: dict[str, Any]
    created_at: datetime
    updated_at: datetime | None = None
