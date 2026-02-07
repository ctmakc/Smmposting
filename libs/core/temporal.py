"""Temporal client management."""

import structlog
from temporalio.client import Client

from libs.core.config import get_settings

logger = structlog.get_logger()

_client: Client | None = None


async def get_temporal_client() -> Client:
    """Get or create a singleton Temporal client."""
    global _client
    if _client is None:
        settings = get_settings()
        logger.info(
            "connecting_to_temporal",
            host=settings.temporal_host,
            namespace=settings.temporal_namespace,
        )
        _client = await Client.connect(
            settings.temporal_host,
            namespace=settings.temporal_namespace,
        )
    return _client


async def close_temporal_client() -> None:
    """Close the Temporal client connection."""
    global _client
    if _client is not None:
        _client = None
