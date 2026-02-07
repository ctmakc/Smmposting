"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.api.routes import brands, health, policies
from libs.core.config import get_settings
from libs.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    setup_logging(settings.log_level)
    yield


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
    return app


app = create_app()
