"""Policy model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libs.db.base import Base


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    forbidden_topics: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    forbidden_claim_patterns: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    competitor_rules: Mapped[dict] = mapped_column(JSON, default=dict)
    risk_threshold_auto_publish: Mapped[int] = mapped_column(Integer, default=50)
    vocabulary: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    brand = relationship("Brand", back_populates="policies")
