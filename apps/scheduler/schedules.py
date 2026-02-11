"""Temporal schedule definitions for periodic workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta


@dataclass
class ScheduleConfig:
    """Configuration for a single Temporal schedule."""

    schedule_id: str
    cron: str  # Temporal cron expression (e.g. "0 */6 * * *")
    workflow_type: str  # Workflow class name
    task_queue: str
    args: dict = field(default_factory=dict)
    memo: dict = field(default_factory=dict)
    execution_timeout: timedelta = field(default_factory=lambda: timedelta(minutes=30))
    overlap_policy: str = "SKIP"  # SKIP, BUFFER_ONE, BUFFER_ALL, CANCEL_OTHER


# Default schedules — can be overridden per brand via API
DEFAULT_SCHEDULES: list[ScheduleConfig] = [
    ScheduleConfig(
        schedule_id="ingest-every-6h",
        cron="0 */6 * * *",
        workflow_type="TrendIngestWorkflow",
        task_queue="ingest",
        memo={"description": "Fetch trending content every 6 hours"},
    ),
    ScheduleConfig(
        schedule_id="planning-every-12h",
        cron="0 */12 * * *",
        workflow_type="ContentPlanningWorkflow",
        task_queue="analyze",
        memo={"description": "Run content planning every 12 hours"},
    ),
]
