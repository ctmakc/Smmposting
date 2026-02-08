"""Generate worker runner — starts Temporal worker for the generate task queue."""

import asyncio

import structlog

from apps.worker_generate.activities import (
    generate_script_activity,
    qc_check_activity,
    rewrite_script_activity,
)
from apps.worker_generate.workflows import TASK_QUEUE, ScriptGenerationWorkflow
from libs.core.config import get_settings
from libs.core.logging import setup_logging
from libs.core.temporal import get_temporal_client

logger = structlog.get_logger()


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)

    logger.info("generate_worker_starting", task_queue=TASK_QUEUE)
    client = await get_temporal_client()

    from temporalio.worker import Worker

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[ScriptGenerationWorkflow],
        activities=[generate_script_activity, qc_check_activity, rewrite_script_activity],
    )

    logger.info("generate_worker_running", task_queue=TASK_QUEUE)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
