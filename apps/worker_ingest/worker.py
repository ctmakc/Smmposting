"""Ingest worker runner — starts Temporal worker for the ingest task queue."""

import asyncio

import structlog

from apps.worker_ingest.activities import fetch_trending_activity, store_sources_activity
from apps.worker_ingest.workflows import TASK_QUEUE, TrendIngestWorkflow
from libs.core.config import get_settings
from libs.core.logging import setup_logging
from libs.core.temporal import get_temporal_client

logger = structlog.get_logger()


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)

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
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
