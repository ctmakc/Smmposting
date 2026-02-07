"""Script model — generated content scripts."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libs.db.base import Base
from libs.db.enums import QCStatus


class Script(Base):
    __tablename__ = "scripts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idea_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    hook_variants: Mapped[dict] = mapped_column(JSON, default=list)
    script_sections: Mapped[dict] = mapped_column(JSON, default=dict)
    on_screen_text: Mapped[dict] = mapped_column(JSON, default=dict)
    broll_list: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    qc_status: Mapped[QCStatus] = mapped_column(default=QCStatus.PENDING)
    qc_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    generation_meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    idea = relationship("Idea", back_populates="scripts")
    assets = relationship("Asset", back_populates="script", lazy="selectin")
    posts = relationship("Post", back_populates="script", lazy="selectin")
