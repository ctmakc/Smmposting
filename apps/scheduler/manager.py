"""Schedule manager — creates, lists, pauses, and deletes Temporal schedules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from temporalio.client import Client

    from apps.scheduler.schedules import ScheduleConfig

logger = structlog.get_logger()


@dataclass
class ScheduleStatus:
    """Status of a Temporal schedule."""

    schedule_id: str
    running: bool
    paused: bool
    info: dict


class ScheduleManager:
    """Manages Temporal cron schedules.

    Uses the Temporal Schedule API (temporalio SDK >= 1.4).
    """

    def __init__(self, client: Client) -> None:
        self._client = client

    async def create_schedule(
        self,
        config: ScheduleConfig,
        *,
        brand_id: str = "",
        brand_name: str = "",
        niches: list[str] | None = None,
        platforms: list[str] | None = None,
    ) -> str:
        """Create a Temporal schedule from config.

        Returns the schedule handle ID.
        """
        from temporalio.client import (
            Schedule,
            ScheduleActionStartWorkflow,
            ScheduleOverlapPolicy,
            SchedulePolicy,
            ScheduleSpec,
            ScheduleState,
        )

        # Build workflow args based on workflow type
        workflow_args = self._build_workflow_args(
            config, brand_id=brand_id, brand_name=brand_name,
            niches=niches or [], platforms=platforms or [],
        )

        # Map overlap policy
        overlap_map = {
            "SKIP": ScheduleOverlapPolicy.SKIP,
            "BUFFER_ONE": ScheduleOverlapPolicy.BUFFER_ONE,
            "BUFFER_ALL": ScheduleOverlapPolicy.BUFFER_ALL,
            "CANCEL_OTHER": ScheduleOverlapPolicy.CANCEL_OTHER,
        }
        overlap = overlap_map.get(config.overlap_policy, ScheduleOverlapPolicy.SKIP)

        # Parse cron to interval (Temporal schedules support both cron and interval)
        schedule_id = f"{config.schedule_id}-{brand_id}" if brand_id else config.schedule_id

        schedule = Schedule(
            action=ScheduleActionStartWorkflow(
                config.workflow_type,
                arg=workflow_args,
                id=f"{schedule_id}-{{{{.ScheduledTime.Format `20060102T150405`}}}}",
                task_queue=config.task_queue,
                execution_timeout=config.execution_timeout,
            ),
            spec=ScheduleSpec(
                cron_expressions=[config.cron],
            ),
            policy=SchedulePolicy(overlap=overlap),
            state=ScheduleState(note=config.memo.get("description", "")),
        )

        await self._client.create_schedule(
            schedule_id,
            schedule,
        )

        logger.info(
            "schedule_created",
            schedule_id=schedule_id,
            cron=config.cron,
            workflow=config.workflow_type,
        )
        return schedule_id

    async def pause_schedule(self, schedule_id: str, *, note: str = "Paused via API") -> None:
        """Pause a Temporal schedule."""
        handle = self._client.get_schedule_handle(schedule_id)
        await handle.pause(note=note)
        logger.info("schedule_paused", schedule_id=schedule_id)

    async def unpause_schedule(self, schedule_id: str, *, note: str = "Unpaused via API") -> None:
        """Resume a paused Temporal schedule."""
        handle = self._client.get_schedule_handle(schedule_id)
        await handle.unpause(note=note)
        logger.info("schedule_unpaused", schedule_id=schedule_id)

    async def delete_schedule(self, schedule_id: str) -> None:
        """Delete a Temporal schedule."""
        handle = self._client.get_schedule_handle(schedule_id)
        await handle.delete()
        logger.info("schedule_deleted", schedule_id=schedule_id)

    async def describe_schedule(self, schedule_id: str) -> ScheduleStatus:
        """Get the status of a Temporal schedule."""
        handle = self._client.get_schedule_handle(schedule_id)
        desc = await handle.describe()

        return ScheduleStatus(
            schedule_id=schedule_id,
            running=bool(desc.info.running_actions),
            paused=desc.schedule.state.paused if desc.schedule.state else False,
            info={
                "num_actions": desc.info.num_actions,
                "num_actions_skipped": desc.info.num_actions_missed_catchup_window,
                "recent_actions": len(desc.info.recent_actions),
                "next_action_times": [
                    t.isoformat() for t in (desc.info.next_action_times or [])[:3]
                ],
            },
        )

    async def list_schedules(self) -> list[ScheduleStatus]:
        """List all schedules in the namespace."""
        schedules: list[ScheduleStatus] = []
        async for entry in self._client.list_schedules():
            schedules.append(
                ScheduleStatus(
                    schedule_id=entry.id,
                    running=bool(entry.info.running_actions) if entry.info else False,
                    paused=entry.info.paused if entry.info else False,
                    info={
                        "num_actions": entry.info.num_actions if entry.info else 0,
                    },
                )
            )
        return schedules

    def _build_workflow_args(
        self,
        config: ScheduleConfig,
        *,
        brand_id: str,
        brand_name: str,
        niches: list[str],
        platforms: list[str],
    ) -> dict:
        """Build workflow input args based on the workflow type."""
        base_args = dict(config.args)

        if config.workflow_type == "TrendIngestWorkflow":
            return {
                "brand_id": brand_id,
                "niches": niches or base_args.get("niches", ["tech"]),
                "platforms": platforms or base_args.get("platforms", ["tiktok", "youtube"]),
                "limit_per_niche": base_args.get("limit_per_niche", 10),
            }

        if config.workflow_type == "ContentPlanningWorkflow":
            return {
                "brand_id": brand_id,
                "brand_name": brand_name,
                "niches": niches or base_args.get("niches", ["tech"]),
                "locale": base_args.get("locale", "en"),
                "forbidden_topics": base_args.get("forbidden_topics", []),
                "num_ideas": base_args.get("num_ideas", 5),
            }

        # Generic fallback
        return base_args
