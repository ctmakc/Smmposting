"""FastAPI dependencies."""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.repositories.asset import AssetRepository
from libs.db.repositories.brand import BrandRepository
from libs.db.repositories.idea import IdeaRepository
from libs.db.repositories.metrics import MetricsRepository
from libs.db.repositories.policy import PolicyRepository
from libs.db.repositories.post import PostRepository
from libs.db.repositories.run import RunRepository
from libs.db.repositories.script import ScriptRepository
from libs.db.session import get_async_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_async_session():
        yield session


async def get_brand_repo(
    session: AsyncSession = Depends(get_db),
) -> BrandRepository:
    return BrandRepository(session)


async def get_policy_repo(
    session: AsyncSession = Depends(get_db),
) -> PolicyRepository:
    return PolicyRepository(session)


async def get_idea_repo(
    session: AsyncSession = Depends(get_db),
) -> IdeaRepository:
    return IdeaRepository(session)


async def get_script_repo(
    session: AsyncSession = Depends(get_db),
) -> ScriptRepository:
    return ScriptRepository(session)


async def get_post_repo(
    session: AsyncSession = Depends(get_db),
) -> PostRepository:
    return PostRepository(session)


async def get_asset_repo(
    session: AsyncSession = Depends(get_db),
) -> AssetRepository:
    return AssetRepository(session)


async def get_metrics_repo(
    session: AsyncSession = Depends(get_db),
) -> MetricsRepository:
    return MetricsRepository(session)


async def get_run_repo(
    session: AsyncSession = Depends(get_db),
) -> RunRepository:
    return RunRepository(session)
