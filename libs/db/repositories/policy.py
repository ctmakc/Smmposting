"""Policy repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.policy import Policy
from libs.db.repositories.base import BaseRepository


class PolicyRepository(BaseRepository[Policy]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Policy)

    async def get_by_brand_id(self, brand_id: uuid.UUID) -> list[Policy]:
        stmt = select(Policy).where(Policy.brand_id == brand_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
