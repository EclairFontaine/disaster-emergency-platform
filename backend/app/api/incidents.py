import math
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional, List
import base64

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.all import Incident, IncidentReport, User
from app.schemas.all import (
    IncidentCreate, IncidentResponse, IncidentUpdate, IncidentStatusUpdate,
    IncidentReportCreate, IncidentReportResponse,
)
from app.services.incident_fsm import validate_transition
from app.services.audit import log_action
from app.api.websocket import broadcast_event

router = APIRouter(prefix="/api/incidents", tags=["灾情管理"])


def haversine(lat1, lng1, lat2, lng2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    data: IncidentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    incident = Incident(
        title=data.title,
        description=data.description,
        category=data.category,
        severity=data.severity,
        latitude=data.latitude,
        longitude=data.longitude,
        affected_count=data.affected_count,
        reported_by=user.id,
    )
    db.add(incident)
    await db.flush()
    await db.refresh(incident)

    await log_action(db, user.id, "create", "incident", incident.id)

    return IncidentResponse.model_validate(incident)


@router.get("", response_model=List[IncidentResponse])
async def list_incidents(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conditions = []
    if status:
        conditions.append(Incident.status == status)
    if category:
        conditions.append(Incident.category == category)
    if severity:
        conditions.append(Incident.severity == severity)

    query = select(Incident)
    if conditions:
        query = query.where(and_(*conditions))
    query = query.order_by(Incident.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    incidents = result.scalars().all()
    return [IncidentResponse.model_validate(i) for i in incidents]


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="灾情不存在")
    return IncidentResponse.model_validate(incident)


@router.put("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: int,
    data: IncidentUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="灾情不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(incident, key, value)

    await db.flush()
    await db.refresh(incident)
    await log_action(db, user.id, "update", "incident", incident_id, update_data)

    return IncidentResponse.model_validate(incident)


@router.put("/{incident_id}/status", response_model=IncidentResponse)
async def update_status(
    incident_id: int,
    data: IncidentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="灾情不存在")

    if not validate_transition(incident.status, data.status):
        raise HTTPException(status_code=400, detail=f"不能从 {incident.status} 变更为 {data.status}")

    old_status = incident.status
    incident.status = data.status

    if data.status == "confirmed":
        incident.confirmed_by = user.id
        from datetime import datetime, timezone
        incident.confirmed_at = datetime.now(timezone.utc)
    elif data.status == "closed":
        from datetime import datetime, timezone
        incident.resolved_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(incident)
    await log_action(db, user.id, "status_change", "incident", incident_id, {"from": old_status, "to": data.status, "reason": data.reason})

    resp = IncidentResponse.model_validate(incident)
    try:
        await broadcast_event("incident:status", resp.model_dump())
    except Exception:
        pass
    return resp


@router.get("/nearby", response_model=List[IncidentResponse])
async def get_nearby_incidents(
    lat: float = Query(...),
    lng: float = Query(...),
    radius: float = Query(10000, description="半径(米)"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Incident))
    all_incidents = result.scalars().all()
    nearby = []
    for inc in all_incidents:
        if inc.latitude and inc.longitude:
            dist = haversine(lat, lng, inc.latitude, inc.longitude)
            if dist <= radius:
                nearby.append(IncidentResponse.model_validate(inc))
    return nearby


@router.post("/{incident_id}/reports", response_model=IncidentReportResponse, status_code=201)
async def create_report(
    incident_id: int,
    data: IncidentReportCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="灾情不存在")

    report = IncidentReport(
        incident_id=incident_id,
        reporter_id=user.id,
        content=data.content,
        images=data.images,
        contact_info=data.contact_info,
        latitude=data.latitude,
        longitude=data.longitude,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)
    return IncidentReportResponse.model_validate(report)


@router.get("/{incident_id}/reports", response_model=List[IncidentReportResponse])
async def list_reports(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(IncidentReport).where(IncidentReport.incident_id == incident_id).order_by(IncidentReport.created_at.desc())
    )
    return [IncidentReportResponse.model_validate(r) for r in result.scalars().all()]


@router.post("/{incident_id}/upload")
async def upload_image(
    incident_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contents = await file.read()
    b64 = base64.b64encode(contents).decode("utf-8")
    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "png"
    data_url = f"data:image/{ext};base64,{b64}"
    return {"url": data_url, "filename": file.filename}
