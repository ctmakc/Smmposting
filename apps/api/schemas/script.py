"""Script API schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from libs.db.enums import QCStatus  # noqa: TCH001


class ScriptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    idea_id: uuid.UUID
    version: int
    hook_variants: Any
    script_sections: dict[str, Any]
    on_screen_text: dict[str, Any]
    broll_list: list[str]
    qc_status: QCStatus
    qc_notes: str | None = None
    generation_meta: dict[str, Any]
    created_at: datetime
    updated_at: datetime | None = None
