"""Health check and metrics endpoints."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Basic liveness probe."""
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness_check() -> dict:
    """Readiness probe — checks DB and Temporal connectivity."""
    checks: dict[str, str] = {}

    # Check DB
    try:
        from sqlalchemy import text

        from libs.db.session import async_session

        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"

    # Check Temporal
    try:
        from libs.core.temporal import get_temporal_client

        client = await get_temporal_client()
        await client.service_client.check_health()
        checks["temporal"] = "ok"
    except Exception as exc:
        checks["temporal"] = f"error: {exc}"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ready" if all_ok else "degraded", "checks": checks}


@router.get("/health/metrics")
async def app_metrics() -> dict:
    """In-process request metrics snapshot."""
    from libs.core.middleware import get_metrics_snapshot

    return get_metrics_snapshot()
