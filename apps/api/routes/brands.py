"""Brand CRUD endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException

from apps.api.deps import get_brand_repo
from apps.api.schemas.brand import BrandCreate, BrandResponse, BrandUpdate
from libs.db.repositories.brand import BrandRepository

router = APIRouter()


@router.get("/", response_model=list[BrandResponse])
async def list_brands(
    offset: int = 0,
    limit: int = 100,
    repo: BrandRepository = Depends(get_brand_repo),
) -> list[BrandResponse]:
    brands = await repo.list_all(offset=offset, limit=limit)
    return [BrandResponse.model_validate(b) for b in brands]


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: uuid.UUID,
    repo: BrandRepository = Depends(get_brand_repo),
) -> BrandResponse:
    brand = await repo.get_by_id(brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")
    return BrandResponse.model_validate(brand)


@router.post("/", response_model=BrandResponse, status_code=201)
async def create_brand(
    body: BrandCreate,
    repo: BrandRepository = Depends(get_brand_repo),
) -> BrandResponse:
    brand = await repo.create(**body.model_dump())
    return BrandResponse.model_validate(brand)


@router.patch("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: uuid.UUID,
    body: BrandUpdate,
    repo: BrandRepository = Depends(get_brand_repo),
) -> BrandResponse:
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    brand = await repo.update(brand_id, **updates)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")
    return BrandResponse.model_validate(brand)


@router.delete("/{brand_id}", status_code=204)
async def delete_brand(
    brand_id: uuid.UUID,
    repo: BrandRepository = Depends(get_brand_repo),
) -> None:
    deleted = await repo.delete(brand_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Brand not found")
