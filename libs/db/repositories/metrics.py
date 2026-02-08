"""Metrics repository."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from libs.db.models.metrics import Metrics

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

    from libs.db.enums import MetricsWindow

from libs.db.repositories.base import BaseRepository


class MetricsRepository(BaseRepository[Metrics]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Metrics)

    async def get_by_post_id(
        self, post_id: uuid.UUID, *, window: MetricsWindow | None = None
    ) -> list[Metrics]:
        stmt = select(Metrics).where(Metrics.post_id == post_id)
        if window is not None:
            stmt = stmt.where(Metrics.window == window)
        stmt = stmt.order_by(Metrics.collected_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_window(self, window: MetricsWindow) -> list[Metrics]:
        stmt = (
            select(Metrics)
            .where(Metrics.window == window)
            .order_by(Metrics.collected_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
