from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.all import AgentRun, Citation, User
from app.schemas.all import AgentRunResponse, CitationResponse
from app.services.agent_runner import create_agent_run, finish_agent_run

router = APIRouter(prefix="/api/agent", tags=["Agent管理"])


@router.get("/runs", response_model=List[AgentRunResponse])
async def list_agent_runs(
    incident_id: Optional[int] = Query(None),
    run_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conditions = []
    if incident_id:
        conditions.append(AgentRun.incident_id == incident_id)
    if run_type:
        conditions.append(AgentRun.run_type == run_type)
    if status:
        conditions.append(AgentRun.status == status)

    from sqlalchemy import and_
    query = select(AgentRun)
    if conditions:
        query = query.where(and_(*conditions))
    query = query.order_by(AgentRun.started_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return [AgentRunResponse.model_validate(r) for r in result.scalars().all()]


@router.get("/runs/{run_id}")
async def get_agent_run_detail(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Agent任务不存在")

    result2 = await db.execute(select(Citation).where(Citation.agent_run_id == run_id))
    citations = [CitationResponse.model_validate(c) for c in result2.scalars().all()]

    return {
        "run": AgentRunResponse.model_validate(run),
        "citations": citations,
    }


@router.post("/runs/{run_id}/retry")
async def retry_agent_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    result = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Agent任务不存在")
    if run.status != "failed":
        raise HTTPException(status_code=400, detail="只能重试失败的任务")

    from app.services.agent_runner import run_plan_generation, run_extraction
    if run.run_type == "generate":
        await run_plan_generation(db, run.incident_id)
    elif run.run_type == "extract":
        await run_extraction(db, run.incident_id)
    else:
        raise HTTPException(status_code=400, detail="不支持重试该类型的任务")

    return {"success": True}
