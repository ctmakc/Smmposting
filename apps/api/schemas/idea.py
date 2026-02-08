"""Idea API schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from libs.db.enums import IdeaStatus  # noqa: TCH001


class IdeaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    title: str
    angle: str | None = None
    persona: str | None = None
    format: str | None = None
    priority_score: float
    risk_score: float
    effort_score: float
    pattern_id: uuid.UUID | None = None
    status: IdeaStatus
    created_at: datetime
    updated_at: datetime | None = None
