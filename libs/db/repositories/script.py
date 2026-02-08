"""Script repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.enums import QCStatus
from libs.db.models.script import Script
from libs.db.repositories.base import BaseRepository


class ScriptRepository(BaseRepository[Script]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Script)

    async def get_by_idea_id(self, idea_id: uuid.UUID) -> list[Script]:
        stmt = select(Script).where(Script.idea_id == idea_id).order_by(Script.version.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending_approval(self) -> list[Script]:
        stmt = select(Script).where(Script.qc_status == QCStatus.REJECTED)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
