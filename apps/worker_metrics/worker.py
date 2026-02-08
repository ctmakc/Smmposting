"""Metrics worker runner — starts Temporal worker for the metrics task queue."""

import asyncio

import structlog

from apps.worker_metrics.activities import (
    evaluate_effectiveness_activity,
    fetch_metrics_activity,
    generate_followup_ideas_activity,
    store_metrics_activity,
    update_pattern_activity,
)
from apps.worker_metrics.workflows import TASK_QUEUE, MetricsCollectionWorkflow
from libs.core.config import get_settings
from libs.core.logging import setup_logging
from libs.core.temporal import get_temporal_client

logger = structlog.get_logger()


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)

    logger.info("metrics_worker_starting", task_queue=TASK_QUEUE)
    client = await get_temporal_client()

    from temporalio.worker import Worker

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[MetricsCollectionWorkflow],
        activities=[
            fetch_metrics_activity,
            store_metrics_activity,
            evaluate_effectiveness_activity,
            update_pattern_activity,
            generate_followup_ideas_activity,
        ],
    )

    logger.info("metrics_worker_running", task_queue=TASK_QUEUE)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
