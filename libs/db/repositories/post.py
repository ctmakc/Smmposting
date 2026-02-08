"""Post repository."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from libs.db.enums import PublishStatus

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.post import Post
from libs.db.repositories.base import BaseRepository


class PostRepository(BaseRepository[Post]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Post)

    async def get_by_brand_id(
        self, brand_id: uuid.UUID, *, status: PublishStatus | None = None
    ) -> list[Post]:
        stmt = select(Post).where(Post.brand_id == brand_id)
        if status is not None:
            stmt = stmt.where(Post.publish_status == status)
        stmt = stmt.order_by(Post.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_script_id(self, script_id: uuid.UUID) -> list[Post]:
        stmt = (
            select(Post)
            .where(Post.script_id == script_id)
            .order_by(Post.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_scheduled(self) -> list[Post]:
        stmt = (
            select(Post)
            .where(Post.publish_status == PublishStatus.SCHEDULED)
            .order_by(Post.scheduled_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_status(self, status: PublishStatus) -> list[Post]:
        stmt = select(Post).where(Post.publish_status == status).order_by(Post.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
