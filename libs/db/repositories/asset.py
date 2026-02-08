"""Asset repository."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from libs.db.models.asset import Asset

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.repositories.base import BaseRepository


class AssetRepository(BaseRepository[Asset]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Asset)

    async def get_by_script_id(self, script_id: uuid.UUID) -> list[Asset]:
        stmt = select(Asset).where(Asset.script_id == script_id).order_by(Asset.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_type(self, script_id: uuid.UUID, asset_type: str) -> list[Asset]:
        stmt = (
            select(Asset)
            .where(Asset.script_id == script_id, Asset.type == asset_type)
            .order_by(Asset.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
