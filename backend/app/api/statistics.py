from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.all import Incident, Resource, DispatchOrder, User
from app.schemas.all import StatisticsResponse, IncidentResponse

router = APIRouter(prefix="/api/statistics", tags=["数据统计"])


@router.get("/", response_model=StatisticsResponse)
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    total_incidents = (await db.execute(select(func.count(Incident.id)))).scalar() or 0
    active_incidents = (await db.execute(
        select(func.count(Incident.id)).where(Incident.status.in_(["confirmed", "in_progress"]))
    )).scalar() or 0
    total_resources = (await db.execute(select(func.count(Resource.id)))).scalar() or 0
    dispatched_resources = (await db.execute(
        select(func.count(DispatchOrder.id)).where(DispatchOrder.status.in_(["approved", "in_transit"]))
    )).scalar() or 0

    cat_result = await db.execute(
        select(Incident.category, func.count(Incident.id)).group_by(Incident.category)
    )
    incidents_by_category = {row[0] or "未分类": row[1] for row in cat_result.all()}

    sev_result = await db.execute(
        select(Incident.severity, func.count(Incident.id)).group_by(Incident.severity)
    )
    incidents_by_severity = {row[0]: row[1] for row in sev_result.all()}

    recent = (await db.execute(
        select(Incident).order_by(Incident.created_at.desc()).limit(10)
    )).scalars().all()

    return StatisticsResponse(
        total_incidents=total_incidents,
        active_incidents=active_incidents,
        total_resources=total_resources,
        dispatched_resources=dispatched_resources,
        incidents_by_category=incidents_by_category,
        incidents_by_severity=incidents_by_severity,
        recent_incidents=[IncidentResponse.model_validate(i) for i in recent],
    )
