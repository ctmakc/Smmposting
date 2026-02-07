"""Brand API schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BrandCreate(BaseModel):
    name: str
    timezone: str = "UTC"
    default_locale: str = "en"
    niches: list[str] = []
    platforms_enabled: list[str] = []


class BrandUpdate(BaseModel):
    name: str | None = None
    timezone: str | None = None
    default_locale: str | None = None
    niches: list[str] | None = None
    platforms_enabled: list[str] | None = None


class BrandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    timezone: str
    default_locale: str
    niches: list[str]
    platforms_enabled: list[str]
    created_at: datetime
    updated_at: datetime | None = None
