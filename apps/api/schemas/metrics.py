"""Metrics and Run API schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from libs.db.enums import MetricsWindow, RunStatus  # noqa: TCH001


class MetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    post_id: uuid.UUID
    window: MetricsWindow
    views: int
    watch_time: float
    retention: float
    ctr: float
    comments: int
    shares: int
    saves: int
    sentiment: float
    top_questions: list[str]
    collected_at: datetime


class RunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workflow_id: str
    trigger_type: str
    started_at: datetime
    finished_at: datetime | None = None
    status: RunStatus
    errors: dict[str, Any] | None = None
