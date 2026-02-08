"""Analyze worker runner — starts Temporal worker for the analyze task queue."""

import asyncio

import structlog

from apps.worker_analyze.activities import analyze_gaps_activity, generate_ideas_activity
from apps.worker_analyze.workflows import TASK_QUEUE, ContentPlanningWorkflow
from libs.core.config import get_settings
from libs.core.logging import setup_logging
from libs.core.temporal import get_temporal_client

logger = structlog.get_logger()


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)

    logger.info("analyze_worker_starting", task_queue=TASK_QUEUE)
    client = await get_temporal_client()

    from temporalio.worker import Worker

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[ContentPlanningWorkflow],
        activities=[analyze_gaps_activity, generate_ideas_activity],
    )

    logger.info("analyze_worker_running", task_queue=TASK_QUEUE)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
