"""Run repository — workflow execution audit log."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from libs.db.models.run import Run

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from libs.db.enums import RunStatus

from libs.db.repositories.base import BaseRepository


class RunRepository(BaseRepository[Run]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Run)

    async def get_by_workflow_id(self, workflow_id: str) -> Run | None:
        stmt = select(Run).where(Run.workflow_id == workflow_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_status(self, status: RunStatus) -> list[Run]:
        stmt = select(Run).where(Run.status == status).order_by(Run.started_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent(self, *, limit: int = 50) -> list[Run]:
        stmt = select(Run).order_by(Run.started_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
