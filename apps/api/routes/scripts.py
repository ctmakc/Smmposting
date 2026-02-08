"""Script read + approval endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException

from apps.api.deps import get_script_repo
from apps.api.schemas.post import ApproveScriptRequest, RejectScriptRequest
from apps.api.schemas.script import ScriptResponse
from libs.db.enums import QCStatus
from libs.db.repositories.script import ScriptRepository

router = APIRouter()


@router.get("/", response_model=list[ScriptResponse])
async def list_scripts(
    idea_id: uuid.UUID | None = None,
    offset: int = 0,
    limit: int = 100,
    repo: ScriptRepository = Depends(get_script_repo),
) -> list[ScriptResponse]:
    if idea_id:
        scripts = await repo.get_by_idea_id(idea_id)
    else:
        scripts = await repo.list_all(offset=offset, limit=limit)
    return [ScriptResponse.model_validate(s) for s in scripts]


@router.get("/pending-approval/", response_model=list[ScriptResponse])
async def list_pending_approval(
    repo: ScriptRepository = Depends(get_script_repo),
) -> list[ScriptResponse]:
    scripts = await repo.get_pending_approval()
    return [ScriptResponse.model_validate(s) for s in scripts]


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: uuid.UUID,
    repo: ScriptRepository = Depends(get_script_repo),
) -> ScriptResponse:
    script = await repo.get_by_id(script_id)
    if script is None:
        raise HTTPException(status_code=404, detail="Script not found")
    return ScriptResponse.model_validate(script)


@router.post("/{script_id}/approve", response_model=ScriptResponse)
async def approve_script(
    script_id: uuid.UUID,
    body: ApproveScriptRequest,
    repo: ScriptRepository = Depends(get_script_repo),
) -> ScriptResponse:
    script = await repo.get_by_id(script_id)
    if script is None:
        raise HTTPException(status_code=404, detail="Script not found")

    qc_notes = body.notes or "Manually approved"
    updated = await repo.update(
        script_id,
        qc_status=QCStatus.APPROVED,
        qc_notes=qc_notes,
    )
    return ScriptResponse.model_validate(updated)


@router.post("/{script_id}/reject", response_model=ScriptResponse)
async def reject_script(
    script_id: uuid.UUID,
    body: RejectScriptRequest,
    repo: ScriptRepository = Depends(get_script_repo),
) -> ScriptResponse:
    script = await repo.get_by_id(script_id)
    if script is None:
        raise HTTPException(status_code=404, detail="Script not found")

    qc_notes = f"Rejected: {body.reason}"
    if body.notes:
        qc_notes += f" — {body.notes}"

    updated = await repo.update(
        script_id,
        qc_status=QCStatus.REJECTED,
        qc_notes=qc_notes,
    )
    return ScriptResponse.model_validate(updated)
