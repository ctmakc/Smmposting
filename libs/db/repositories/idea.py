"""Idea repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.enums import IdeaStatus
from libs.db.models.idea import Idea
from libs.db.repositories.base import BaseRepository


class IdeaRepository(BaseRepository[Idea]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Idea)

    async def get_by_brand_id(
        self, brand_id: uuid.UUID, *, status: IdeaStatus | None = None
    ) -> list[Idea]:
        stmt = select(Idea).where(Idea.brand_id == brand_id)
        if status:
            stmt = stmt.where(Idea.status == status)
        stmt = stmt.order_by(Idea.priority_score.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
