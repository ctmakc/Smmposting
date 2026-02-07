"""Brand model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libs.db.base import Base


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    default_locale: Mapped[str] = mapped_column(String(16), default="en")
    niches: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    platforms_enabled: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    policies = relationship("Policy", back_populates="brand", lazy="selectin")
    ideas = relationship("Idea", back_populates="brand", lazy="selectin")
    patterns = relationship("Pattern", back_populates="brand", lazy="selectin")
    posts = relationship("Post", back_populates="brand", lazy="selectin")
