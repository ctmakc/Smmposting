"""Schedule management endpoints."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from apps.scheduler.manager import ScheduleManager
from apps.scheduler.schedules import DEFAULT_SCHEDULES
from libs.core.temporal import get_temporal_client

logger = structlog.get_logger()

router = APIRouter()


# --- Request/Response schemas ---


class CreateScheduleRequest(BaseModel):
    brand_id: str
    brand_name: str = ""
    niches: list[str] = []
    platforms: list[str] = []
    schedule_id: str | None = None
    cron: str | None = None


class ScheduleResponse(BaseModel):
    schedule_id: str
    running: bool
    paused: bool
    info: dict


class PauseRequest(BaseModel):
    note: str = ""


# --- Endpoints ---


@router.post("/create-defaults", response_model=list[ScheduleResponse], status_code=201)
async def create_default_schedules(body: CreateScheduleRequest) -> list[ScheduleResponse]:
    """Create all default schedules for a brand."""
    client = await get_temporal_client()
    manager = ScheduleManager(client)

    results: list[ScheduleResponse] = []
    for config in DEFAULT_SCHEDULES:
        try:
            schedule_id = await manager.create_schedule(
                config,
                brand_id=body.brand_id,
                brand_name=body.brand_name,
                niches=body.niches,
                platforms=body.platforms,
            )
            desc = await manager.describe_schedule(schedule_id)
            results.append(ScheduleResponse(
                schedule_id=desc.schedule_id,
                running=desc.running,
                paused=desc.paused,
                info=desc.info,
            ))
        except Exception as exc:
            logger.error("schedule_create_failed", schedule_id=config.schedule_id, error=str(exc))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create schedule {config.schedule_id}: {exc}",
            ) from exc

    return results


@router.get("/", response_model=list[ScheduleResponse])
async def list_schedules() -> list[ScheduleResponse]:
    """List all active schedules."""
    client = await get_temporal_client()
    manager = ScheduleManager(client)
    schedules = await manager.list_schedules()
    return [
        ScheduleResponse(
            schedule_id=s.schedule_id,
            running=s.running,
            paused=s.paused,
            info=s.info,
        )
        for s in schedules
    ]


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: str) -> ScheduleResponse:
    """Get the status of a specific schedule."""
    client = await get_temporal_client()
    manager = ScheduleManager(client)
    try:
        desc = await manager.describe_schedule(schedule_id)
    except Exception as exc:
        raise HTTPException(
            status_code=404, detail=f"Schedule not found: {schedule_id}"
        ) from exc

    return ScheduleResponse(
        schedule_id=desc.schedule_id,
        running=desc.running,
        paused=desc.paused,
        info=desc.info,
    )


@router.post("/{schedule_id}/pause", status_code=204)
async def pause_schedule(schedule_id: str, body: PauseRequest | None = None) -> None:
    """Pause a schedule."""
    client = await get_temporal_client()
    manager = ScheduleManager(client)
    note = body.note if body else "Paused via API"
    try:
        await manager.pause_schedule(schedule_id, note=note)
    except Exception as exc:
        raise HTTPException(
            status_code=404, detail=f"Schedule not found: {schedule_id}"
        ) from exc


@router.post("/{schedule_id}/unpause", status_code=204)
async def unpause_schedule(schedule_id: str, body: PauseRequest | None = None) -> None:
    """Resume a paused schedule."""
    client = await get_temporal_client()
    manager = ScheduleManager(client)
    note = body.note if body else "Unpaused via API"
    try:
        await manager.unpause_schedule(schedule_id, note=note)
    except Exception as exc:
        raise HTTPException(
            status_code=404, detail=f"Schedule not found: {schedule_id}"
        ) from exc


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(schedule_id: str) -> None:
    """Delete a schedule."""
    client = await get_temporal_client()
    manager = ScheduleManager(client)
    try:
        await manager.delete_schedule(schedule_id)
    except Exception as exc:
        raise HTTPException(
            status_code=404, detail=f"Schedule not found: {schedule_id}"
        ) from exc
