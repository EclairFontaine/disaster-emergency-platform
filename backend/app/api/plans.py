from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_current_user, require_commander, require_admin
from app.models.all import EmergencyPlan, User, AgentRun, DispatchOrder
from app.schemas.all import (
    EmergencyPlanCreate, EmergencyPlanResponse, EmergencyPlanUpdate,
    PlanSearchRequest, PlanReviewRequest, PlanGenerateRequest,
)
from app.services.rag import search_plans
from app.services.agent_runner import run_plan_generation
from app.services.audit import log_action

router = APIRouter(prefix="/api/plans", tags=["应急预案"])


@router.get("", response_model=List[EmergencyPlanResponse])
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


@router.post("", response_model=EmergencyPlanResponse, status_code=201)
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


async def _run_generation_in_background(incident_id: int, agent_run_id: int):
    """后台运行方案生成，独立 session 不依赖请求 session"""
    print(f"[BG] Starting generation for incident {incident_id}, run {agent_run_id}")
    from app.core.database import AsyncSessionLocal
    from app.services.agent_runner import run_plan_generation
    async with AsyncSessionLocal() as db:
        try:
            await run_plan_generation(db, incident_id)
            print(f"[BG] Generation completed for run {agent_run_id}")
        except Exception as e:
            print(f"[BG] Generation failed: {e}")


@router.post("/generate")
async def generate_plan(
    data: PlanGenerateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.services.agent_runner import run_plan_generation
    run = await run_plan_generation(db, data.incident_id)
    await log_action(db, user.id, "generate_plan", "plan", None, {"incident_id": data.incident_id, "agent_run_id": run.id})
    return {"agent_run_id": run.id, "status": run.status}


@router.get("/generate/{agent_run_id}/stream")
async def stream_plan_generation(
    agent_run_id: int,
):
    import json as json_mod
    import asyncio
    from app.core.database import AsyncSessionLocal

    yield f"data: {json_mod.dumps({'status': 'extracting', 'message': '正在分析灾情...'})}\n\n"

    for i in range(30):
        await asyncio.sleep(0.5)
        async with AsyncSessionLocal() as s:
            from app.models.all import AgentRun as AR
            r = await s.execute(select(AR).where(AR.id == agent_run_id))
            run = r.scalar_one_or_none()
            if not run:
                yield f"data: {json_mod.dumps({'status': 'error', 'message': '任务不存在'})}\n\n"
                return
            if run.status == "completed":
                yield f"data: {json_mod.dumps({'status': 'completed', 'agent_run_id': run.id, 'output_data': run.output_data})}\n\n"
                return
            if run.status == "failed":
                yield f"data: {json_mod.dumps({'status': 'error', 'message': run.error_message or '生成失败'})}\n\n"
                return
        if i == 3:
            yield f"data: {json_mod.dumps({'status': 'retrieving', 'message': '正在检索相关预案...'})}\n\n"
        elif i == 8:
            yield f"data: {json_mod.dumps({'status': 'generating', 'message': '正在生成应急方案...'})}\n\n"

    yield f"data: {json_mod.dumps({'status': 'error', 'message': '生成超时'})}\n\n"


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

    # 批准方案时，自动批准所有关联的待审批调度单
    dispatch_approved = 0
    if data.status == "approved":
        result2 = await db.execute(
            select(DispatchOrder).where(
                DispatchOrder.plan_id == plan_id,
                DispatchOrder.status == "pending",
            )
        )
        pending_orders = result2.scalars().all()
        for order in pending_orders:
            order.status = "approved"
            order.approved_by = user.id
            dispatch_approved += 1
        if dispatch_approved:
            await db.flush()

    await log_action(db, user.id, "review", "plan", plan_id, {"status": data.status, "comment": data.comment, "auto_approved_dispatches": dispatch_approved})
    return EmergencyPlanResponse.model_validate(plan)
