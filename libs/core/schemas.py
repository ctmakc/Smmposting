"""Base Pydantic schemas shared across the application."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema with common config."""

    model_config = ConfigDict(from_attributes=True)


class UUIDSchemaMixin(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)


class TimestampSchemaMixin(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None
