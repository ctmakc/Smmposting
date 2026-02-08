"""Metrics and Runs read endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException

from apps.api.deps import get_metrics_repo, get_run_repo
from apps.api.schemas.metrics import MetricsResponse, RunResponse
from libs.db.enums import MetricsWindow
from libs.db.repositories.metrics import MetricsRepository
from libs.db.repositories.run import RunRepository

router = APIRouter()


# --- Metrics ---


@router.get("/post/{post_id}", response_model=list[MetricsResponse])
async def list_metrics_for_post(
    post_id: uuid.UUID,
    window: MetricsWindow | None = None,
    repo: MetricsRepository = Depends(get_metrics_repo),
) -> list[MetricsResponse]:
    metrics = await repo.get_by_post_id(post_id, window=window)
    return [MetricsResponse.model_validate(m) for m in metrics]


@router.get("/{metrics_id}", response_model=MetricsResponse)
async def get_metrics(
    metrics_id: uuid.UUID,
    repo: MetricsRepository = Depends(get_metrics_repo),
) -> MetricsResponse:
    m = await repo.get_by_id(metrics_id)
    if m is None:
        raise HTTPException(status_code=404, detail="Metrics not found")
    return MetricsResponse.model_validate(m)


# --- Runs ---


@router.get("/runs/", response_model=list[RunResponse])
async def list_runs(
    limit: int = 50,
    repo: RunRepository = Depends(get_run_repo),
) -> list[RunResponse]:
    runs = await repo.get_recent(limit=limit)
    return [RunResponse.model_validate(r) for r in runs]


@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: uuid.UUID,
    repo: RunRepository = Depends(get_run_repo),
) -> RunResponse:
    run = await repo.get_by_id(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunResponse.model_validate(run)
