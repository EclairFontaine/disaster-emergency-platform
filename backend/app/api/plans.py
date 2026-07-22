from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_current_user, require_commander, require_admin
from app.models.all import EmergencyPlan, User, AgentRun
from app.schemas.all import (
    EmergencyPlanCreate, EmergencyPlanResponse, EmergencyPlanUpdate,
    PlanSearchRequest, PlanReviewRequest, PlanGenerateRequest,
)
from app.services.rag import search_plans
from app.services.agent_runner import run_plan_generation, stream_generate_plan
from app.services.audit import log_action

router = APIRouter(prefix="/api/plans", tags=["应急预案"])


@router.get("/", response_model=List[EmergencyPlanResponse])
async def list_plans(
    incident_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(EmergencyPlan)
    if incident_id:
        query = query.where(EmergencyPlan.incident_id == incident_id)
    query = query.order_by(EmergencyPlan.created_at.desc())
    result = await db.execute(query)
    return [EmergencyPlanResponse.model_validate(p) for p in result.scalars().all()]


@router.post("/", response_model=EmergencyPlanResponse, status_code=201)
async def create_plan(
    data: EmergencyPlanCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    plan = EmergencyPlan(
        title=data.title,
        content=data.content,
        incident_id=data.incident_id,
        generated_by="manual",
    )
    db.add(plan)
    await db.flush()
    await db.refresh(plan)
    await log_action(db, user.id, "create", "plan", plan.id)
    return EmergencyPlanResponse.model_validate(plan)


@router.get("/{plan_id}", response_model=EmergencyPlanResponse)
async def get_plan(plan_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(EmergencyPlan).where(EmergencyPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="预案不存在")
    return EmergencyPlanResponse.model_validate(plan)


@router.put("/{plan_id}", response_model=EmergencyPlanResponse)
async def update_plan(
    plan_id: int,
    data: EmergencyPlanUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(EmergencyPlan).where(EmergencyPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="预案不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)
    await db.flush()
    await db.refresh(plan)
    return EmergencyPlanResponse.model_validate(plan)


@router.delete("/{plan_id}", status_code=204)
async def delete_plan(plan_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    result = await db.execute(select(EmergencyPlan).where(EmergencyPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="预案不存在")
    await db.delete(plan)
    await db.flush()


@router.post("/search", response_model=List[EmergencyPlanResponse])
async def search_plans_endpoint(
    data: PlanSearchRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    plans = await search_plans(db, data.query)
    return [EmergencyPlanResponse.model_validate(p) for p in plans]


@router.post("/generate")
async def generate_plan(
    data: PlanGenerateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_commander),
):
    from app.services.agent_runner import create_agent_run
    run = await create_agent_run(db, data.incident_id, "generate", {"incident_id": data.incident_id})
    await log_action(db, user.id, "generate_plan", "plan", None, {"incident_id": data.incident_id, "agent_run_id": run.id})
    return {"agent_run_id": run.id}


@router.get("/generate/{agent_run_id}/stream")
async def stream_plan_generation(
    agent_run_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AgentRun).where(AgentRun.id == agent_run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Agent任务不存在")

    return StreamingResponse(
        stream_generate_plan(db, run.incident_id, agent_run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{plan_id}/review", response_model=EmergencyPlanResponse)
async def review_plan(
    plan_id: int,
    data: PlanReviewRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_commander),
):
    result = await db.execute(select(EmergencyPlan).where(EmergencyPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="预案不存在")

    from datetime import datetime, timezone
    plan.status = data.status
    plan.reviewed_by = user.id
    plan.reviewed_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(plan)

    await log_action(db, user.id, "review", "plan", plan_id, {"status": data.status, "comment": data.comment})
    return EmergencyPlanResponse.model_validate(plan)
