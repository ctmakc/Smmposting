"""Post API schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from libs.db.enums import PublishStatus  # noqa: TCH001


class PostCreate(BaseModel):
    brand_id: uuid.UUID
    script_id: uuid.UUID
    platform: str
    scheduled_at: datetime | None = None
    caption: str | None = None
    hashtags: list[str] = []
    utm_params: dict[str, Any] = {}


class PostUpdate(BaseModel):
    scheduled_at: datetime | None = None
    caption: str | None = None
    hashtags: list[str] | None = None
    utm_params: dict[str, Any] | None = None


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    script_id: uuid.UUID
    platform: str
    scheduled_at: datetime | None = None
    published_at: datetime | None = None
    caption: str | None = None
    hashtags: list[str]
    utm_params: dict[str, Any]
    publish_status: PublishStatus
    url: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class ApproveScriptRequest(BaseModel):
    notes: str | None = None


class RejectScriptRequest(BaseModel):
    reason: str
    notes: str | None = None
