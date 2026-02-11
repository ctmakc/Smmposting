"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.api.routes import (
    brands,
    health,
    ideas,
    metrics,
    policies,
    posts,
    schedules,
    scripts,
    workflows,
)
from libs.core.config import get_settings
from libs.core.logging import setup_logging
from libs.core.middleware import setup_middleware
from libs.core.temporal import close_temporal_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    setup_logging(settings.log_level)
    yield
    await close_temporal_client()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Content Factory API",
        version="0.1.0",
        lifespan=lifespan,
        debug=settings.debug,
    )
    app.include_router(health.router, tags=["health"])
    app.include_router(brands.router, prefix="/brands", tags=["brands"])
    app.include_router(policies.router, prefix="/policies", tags=["policies"])
    app.include_router(ideas.router, prefix="/ideas", tags=["ideas"])
    app.include_router(scripts.router, prefix="/scripts", tags=["scripts"])
    app.include_router(posts.router, prefix="/posts", tags=["posts"])
    app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
    app.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
    app.include_router(schedules.router, prefix="/schedules", tags=["schedules"])
    setup_middleware(app)
    return app


app = create_app()
