"""Policy CRUD endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException

from apps.api.deps import get_policy_repo
from apps.api.schemas.policy import PolicyCreate, PolicyResponse, PolicyUpdate
from libs.db.repositories.policy import PolicyRepository

router = APIRouter()


@router.get("/", response_model=list[PolicyResponse])
async def list_policies(
    brand_id: uuid.UUID | None = None,
    offset: int = 0,
    limit: int = 100,
    repo: PolicyRepository = Depends(get_policy_repo),
) -> list[PolicyResponse]:
    if brand_id:
        policies = await repo.get_by_brand_id(brand_id)
    else:
        policies = await repo.list_all(offset=offset, limit=limit)
    return [PolicyResponse.model_validate(p) for p in policies]


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: uuid.UUID,
    repo: PolicyRepository = Depends(get_policy_repo),
) -> PolicyResponse:
    policy = await repo.get_by_id(policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    return PolicyResponse.model_validate(policy)


@router.post("/", response_model=PolicyResponse, status_code=201)
async def create_policy(
    body: PolicyCreate,
    repo: PolicyRepository = Depends(get_policy_repo),
) -> PolicyResponse:
    policy = await repo.create(**body.model_dump())
    return PolicyResponse.model_validate(policy)


@router.patch("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: uuid.UUID,
    body: PolicyUpdate,
    repo: PolicyRepository = Depends(get_policy_repo),
) -> PolicyResponse:
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    policy = await repo.update(policy_id, **updates)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    return PolicyResponse.model_validate(policy)


@router.delete("/{policy_id}", status_code=204)
async def delete_policy(
    policy_id: uuid.UUID,
    repo: PolicyRepository = Depends(get_policy_repo),
) -> None:
    deleted = await repo.delete(policy_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Policy not found")
