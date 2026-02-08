"""Script read endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException

from apps.api.deps import get_script_repo
from apps.api.schemas.script import ScriptResponse
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


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: uuid.UUID,
    repo: ScriptRepository = Depends(get_script_repo),
) -> ScriptResponse:
    script = await repo.get_by_id(script_id)
    if script is None:
        raise HTTPException(status_code=404, detail="Script not found")
    return ScriptResponse.model_validate(script)


@router.get("/pending-approval/", response_model=list[ScriptResponse])
async def list_pending_approval(
    repo: ScriptRepository = Depends(get_script_repo),
) -> list[ScriptResponse]:
    scripts = await repo.get_pending_approval()
    return [ScriptResponse.model_validate(s) for s in scripts]
