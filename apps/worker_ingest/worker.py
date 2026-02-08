"""Ingest worker runner — starts Temporal worker for the ingest task queue."""

import asyncio

import structlog

from apps.worker_ingest.activities import fetch_trending_activity, store_sources_activity
from apps.worker_ingest.workflows import TASK_QUEUE, TrendIngestWorkflow
from libs.core.config import get_settings
from libs.core.logging import setup_logging
from libs.core.shutdown import setup_signal_handlers
from libs.core.temporal import get_temporal_client

logger = structlog.get_logger()


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)

    shutdown_event = asyncio.Event()
    setup_signal_handlers(shutdown_event)

    logger.info("ingest_worker_starting", task_queue=TASK_QUEUE)
    client = await get_temporal_client()

    from temporalio.worker import Worker

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[TrendIngestWorkflow],
        activities=[fetch_trending_activity, store_sources_activity],
    )

    logger.info("ingest_worker_running", task_queue=TASK_QUEUE)
    async with worker:
        await shutdown_event.wait()
    logger.info("ingest_worker_stopped")


if __name__ == "__main__":
    asyncio.run(main())
