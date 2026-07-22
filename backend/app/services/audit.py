from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.models.all import AuditLog


async def log_action(
    db: AsyncSession,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    detail: dict = None,
    ip_address: str = "",
):
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail or {},
        ip_address=ip_address,
    )
    db.add(log)
    await db.flush()


async def get_audit_logs(
    db: AsyncSession,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
):
    conditions = []
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)
    if resource_id:
        conditions.append(AuditLog.resource_id == resource_id)

    query = select(AuditLog)
    if conditions:
        from sqlalchemy import and_
        query = query.where(and_(*conditions))
    query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
