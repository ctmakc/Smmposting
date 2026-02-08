"""Idea read endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.deps import get_idea_repo
from apps.api.schemas.idea import IdeaResponse
from libs.db.enums import IdeaStatus
from libs.db.repositories.idea import IdeaRepository

router = APIRouter()


@router.get("/", response_model=list[IdeaResponse])
async def list_ideas(
    brand_id: uuid.UUID | None = None,
    status: IdeaStatus | None = Query(default=None),
    offset: int = 0,
    limit: int = 100,
    repo: IdeaRepository = Depends(get_idea_repo),
) -> list[IdeaResponse]:
    if brand_id:
        ideas = await repo.get_by_brand_id(brand_id, status=status)
    else:
        ideas = await repo.list_all(offset=offset, limit=limit)
    return [IdeaResponse.model_validate(i) for i in ideas]


@router.get("/{idea_id}", response_model=IdeaResponse)
async def get_idea(
    idea_id: uuid.UUID,
    repo: IdeaRepository = Depends(get_idea_repo),
) -> IdeaResponse:
    idea = await repo.get_by_id(idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")
    return IdeaResponse.model_validate(idea)
