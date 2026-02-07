"""Brand repository."""

from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.brand import Brand
from libs.db.repositories.base import BaseRepository


class BrandRepository(BaseRepository[Brand]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Brand)
