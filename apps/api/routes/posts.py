"""Post CRUD and publishing endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException

from apps.api.deps import get_post_repo
from apps.api.schemas.post import PostCreate, PostResponse, PostUpdate
from libs.db.enums import PublishStatus
from libs.db.repositories.post import PostRepository

router = APIRouter()


@router.get("/", response_model=list[PostResponse])
async def list_posts(
    brand_id: uuid.UUID | None = None,
    status: PublishStatus | None = None,
    offset: int = 0,
    limit: int = 100,
    repo: PostRepository = Depends(get_post_repo),
) -> list[PostResponse]:
    if brand_id:
        posts = await repo.get_by_brand_id(brand_id, status=status)
    elif status:
        posts = await repo.get_by_status(status)
    else:
        posts = await repo.list_all(offset=offset, limit=limit)
    return [PostResponse.model_validate(p) for p in posts]


@router.get("/scheduled/", response_model=list[PostResponse])
async def list_scheduled(
    repo: PostRepository = Depends(get_post_repo),
) -> list[PostResponse]:
    posts = await repo.get_scheduled()
    return [PostResponse.model_validate(p) for p in posts]


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: uuid.UUID,
    repo: PostRepository = Depends(get_post_repo),
) -> PostResponse:
    post = await repo.get_by_id(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostResponse.model_validate(post)


@router.post("/", response_model=PostResponse, status_code=201)
async def create_post(
    body: PostCreate,
    repo: PostRepository = Depends(get_post_repo),
) -> PostResponse:
    status = PublishStatus.SCHEDULED if body.scheduled_at else PublishStatus.DRAFT
    post = await repo.create(
        brand_id=body.brand_id,
        script_id=body.script_id,
        platform=body.platform,
        scheduled_at=body.scheduled_at,
        caption=body.caption,
        hashtags=body.hashtags,
        utm_params=body.utm_params,
        publish_status=status,
    )
    return PostResponse.model_validate(post)


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: uuid.UUID,
    body: PostUpdate,
    repo: PostRepository = Depends(get_post_repo),
) -> PostResponse:
    existing = await repo.get_by_id(post_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if existing.publish_status not in (PublishStatus.DRAFT, PublishStatus.SCHEDULED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot update post in status '{existing.publish_status.value}'",
        )
    updates = body.model_dump(exclude_none=True)
    post = await repo.update(post_id, **updates)
    return PostResponse.model_validate(post)
