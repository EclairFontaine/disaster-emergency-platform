from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.all import User
from app.schemas.all import AuditLogResponse
from app.services.audit import get_audit_logs

router = APIRouter(prefix="/api/audit", tags=["审计日志"])


@router.get("/", response_model=List[AuditLogResponse])
async def list_audit_logs(
    user_id: Optional[int] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[int] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    logs = await get_audit_logs(db, user_id, resource_type, resource_id, limit, offset)
    return [AuditLogResponse.model_validate(log) for log in logs]
