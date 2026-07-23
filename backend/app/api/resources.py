from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_current_user, require_commander, require_resource_ops
from app.models.all import Resource, DispatchOrder, User, ResourceLock
from app.schemas.all import (
    ResourceCreate, ResourceResponse, ResourceUpdate, ResourceLockRequest,
    DispatchOrderCreate, DispatchOrderResponse, DispatchOrderStatusUpdate,
)
from app.services.resource_scheduler import lock_resource, release_resource, release_incident_resources
from app.services.audit import log_action
from app.api.websocket import broadcast_event

router = APIRouter(prefix="/api", tags=["资源管理"])


@router.get("/resources", response_model=List[ResourceResponse])
async def list_resources(
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conditions = []
    if type:
        conditions.append(Resource.type == type)
    if status:
        conditions.append(Resource.status == status)

    query = select(Resource)
    if conditions:
        query = query.where(and_(*conditions))
    query = query.order_by(Resource.created_at.desc())
    result = await db.execute(query)
    return [ResourceResponse.model_validate(r) for r in result.scalars().all()]


@router.post("/resources", response_model=ResourceResponse, status_code=201)
async def create_resource(
    data: ResourceCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    resource = Resource(**data.model_dump())
    db.add(resource)
    await db.flush()
    await db.refresh(resource)
    await log_action(db, user.id, "create", "resource", resource.id)
    return ResourceResponse.model_validate(resource)


@router.get("/resources/{resource_id}", response_model=ResourceResponse)
async def get_resource(resource_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")
    return ResourceResponse.model_validate(resource)


@router.put("/resources/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: int,
    data: ResourceUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(resource, key, value)
    await db.flush()
    await db.refresh(resource)
    return ResourceResponse.model_validate(resource)


@router.delete("/resources/{resource_id}", status_code=204)
async def delete_resource(resource_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")
    await db.delete(resource)
    await db.flush()


@router.post("/resources/{resource_id}/lock")
async def lock_resource_endpoint(
    resource_id: int,
    data: ResourceLockRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_resource_ops),
):
    success = await lock_resource(db, resource_id, data.incident_id, data.quantity, user.id)
    if not success:
        raise HTTPException(status_code=400, detail="资源不足，锁定失败")
    await log_action(db, user.id, "lock", "resource", resource_id, {"incident_id": data.incident_id, "quantity": data.quantity})
    try:
        await broadcast_event("resource:lock", {"resource_id": resource_id, "incident_id": data.incident_id, "quantity": data.quantity})
    except Exception:
        pass
    return {"success": True}


@router.post("/resources/{resource_id}/release")
async def release_resource_endpoint(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_resource_ops),
):
    result = await db.execute(
        select(ResourceLock).where(
            ResourceLock.resource_id == resource_id,
            ResourceLock.released_at.is_(None),
        )
    )
    locks = result.scalars().all()
    success = False
    for lock in locks:
        if await release_resource(db, lock.id):
            success = True
    if not success:
        raise HTTPException(status_code=400, detail="无可用锁定记录")
    try:
        await broadcast_event("resource:release", {"resource_id": resource_id})
    except Exception:
        pass
    return {"success": True}


@router.get("/dispatch-orders", response_model=List[DispatchOrderResponse])
async def list_dispatch_orders(
    incident_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conditions = []
    if incident_id:
        conditions.append(DispatchOrder.incident_id == incident_id)

    query = select(DispatchOrder)
    if conditions:
        query = query.where(and_(*conditions))
    query = query.order_by(DispatchOrder.created_at.desc())
    result = await db.execute(query)
    return [DispatchOrderResponse.model_validate(o) for o in result.scalars().all()]


@router.post("/dispatch-orders", response_model=DispatchOrderResponse, status_code=201)
async def create_dispatch_order(
    data: DispatchOrderCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_resource_ops),
):
    order = DispatchOrder(**data.model_dump())
    db.add(order)
    await db.flush()
    await db.refresh(order)
    await log_action(db, user.id, "create", "dispatch_order", order.id)
    resp = DispatchOrderResponse.model_validate(order)
    try:
        await broadcast_event("dispatch:created", resp.model_dump())
    except Exception:
        pass
    return resp


@router.get("/dispatch-orders/{order_id}", response_model=DispatchOrderResponse)
async def get_dispatch_order(order_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(DispatchOrder).where(DispatchOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="调度单不存在")
    return DispatchOrderResponse.model_validate(order)


@router.put("/dispatch-orders/{order_id}/status", response_model=DispatchOrderResponse)
async def update_dispatch_status(
    order_id: int,
    data: DispatchOrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_resource_ops),
):
    result = await db.execute(select(DispatchOrder).where(DispatchOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="调度单不存在")

    from datetime import datetime, timezone
    if data.status == "approved":
        order.approved_by = user.id
    elif data.status == "in_transit":
        order.dispatched_at = datetime.now(timezone.utc)
    elif data.status == "arrived":
        order.arrived_at = datetime.now(timezone.utc)

    order.status = data.status
    await db.flush()
    await db.refresh(order)
    await log_action(db, user.id, "update_status", "dispatch_order", order_id, {"status": data.status})
    return DispatchOrderResponse.model_validate(order)
