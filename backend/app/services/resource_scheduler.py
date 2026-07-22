from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.all import Resource, ResourceLock


async def lock_resource(db: AsyncSession, resource_id: int, incident_id: int, quantity: int, user_id: int) -> bool:
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    if not resource:
        return False

    available = resource.available_qty - resource.locked_qty
    if available < quantity:
        return False

    resource.locked_qty += quantity
    lock = ResourceLock(
        resource_id=resource_id,
        incident_id=incident_id,
        quantity=quantity,
        locked_by=user_id,
    )
    db.add(lock)
    await db.flush()
    return True


async def release_resource(db: AsyncSession, lock_id: int) -> bool:
    result = await db.execute(select(ResourceLock).where(ResourceLock.id == lock_id))
    lock = result.scalar_one_or_none()
    if not lock or lock.released_at is not None:
        return False

    result2 = await db.execute(select(Resource).where(Resource.id == lock.resource_id))
    resource = result2.scalar_one_or_none()
    if resource:
        resource.locked_qty = max(0, resource.locked_qty - lock.quantity)

    lock.released_at = datetime.now(timezone.utc)
    await db.flush()
    return True


async def release_incident_resources(db: AsyncSession, incident_id: int):
    result = await db.execute(
        select(ResourceLock).where(ResourceLock.incident_id == incident_id, ResourceLock.released_at.is_(None))
    )
    locks = result.scalars().all()
    for lock in locks:
        await release_resource(db, lock.id)


async def check_conflict(db: AsyncSession, resource_id: int, quantity: int) -> bool:
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    if not resource:
        return True
    return (resource.available_qty - resource.locked_qty) < quantity
