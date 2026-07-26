import asyncio
import json as json_mod
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from database import get_db, AsyncSessionLocal
from models import AgentRun, Citation
from clients.deepseek import deepseek_client, SYSTEM_PROMPTS
from engines.plan_generator import generate_plan

router = APIRouter(prefix="/api/v1", tags=["AI Agent"])


class PlanGenerateRequest(BaseModel):
    incident_id: int
    incident: dict
    matched_plans: list[dict] = []
    historical_events: list[dict] = []


class ExtractRequest(BaseModel):
    title: str
    description: str = ""


class ReviewRequest(BaseModel):
    plan_content: str


class RunResponse(BaseModel):
    id: int
    incident_id: int
    run_type: str
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    status: str
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    class Config:
        from_attributes = True


def _serialize_run(run: AgentRun) -> dict:
    return {
        "id": run.id,
        "incident_id": run.incident_id,
        "run_type": run.run_type,
        "input_data": run.input_data,
        "output_data": run.output_data,
        "status": run.status,
        "error_message": run.error_message,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }


@router.get("/health")
async def health_check():
    dify_ok = False
    try:
        from config import settings
        dify_ok = bool(settings.DIFY_API_KEY and settings.DIFY_API_KEY not in ("app-placeholder", ""))
    except Exception:
        pass
    return {
        "status": "ok",
        "service": "ai-service",
        "providers": {
            "deepseek": "configured",
            "dify": "configured" if dify_ok else "unavailable",
        },
    }


@router.post("/generate-plan")
async def generate_plan_endpoint(data: PlanGenerateRequest, db: AsyncSession = Depends(get_db)):
    run = AgentRun(
        incident_id=data.incident_id,
        run_type="generate",
        input_data={
            "incident": data.incident.get("title", ""),
            "provider_hint": "auto_detect",
        },
        status="running",
    )
    db.add(run)
    await db.flush()
    await db.refresh(run)

    try:
        result = await generate_plan(data.incident, data.matched_plans, data.historical_events)

        run.output_data = {
            "plan_content": result["plan_content"],
            "source_refs": result["source_refs"],
            "provider": result["provider"],
        }
        run.status = "completed"
        run.finished_at = datetime.now(timezone.utc)
        await db.flush()

        return {
            "run_id": run.id,
            "status": "completed",
            "plan_content": result["plan_content"],
            "source_refs": result["source_refs"],
            "citations": result["citations"],
            "provider": result["provider"],
        }
    except Exception as e:
        run.status = "failed"
        run.error_message = str(e)
        run.finished_at = datetime.now(timezone.utc)
        await db.flush()
        return {
            "run_id": run.id,
            "status": "failed",
            "error": str(e),
        }


@router.post("/generate-plan/stream")
async def generate_plan_stream(data: PlanGenerateRequest):
    async def event_stream():
        try:
            async with AsyncSessionLocal() as db:
                run = AgentRun(
                    incident_id=data.incident_id,
                    run_type="generate",
                    input_data={"incident": data.incident.get("title", "")},
                    status="running",
                )
                db.add(run)
                await db.flush()
                await db.refresh(run)
                run_id = run.id
                await db.commit()

            yield f"data: {json_mod.dumps({'status': 'extracting', 'message': '正在分析灾情信息...'})}\n\n"
            await asyncio.sleep(0.3)
            yield f"data: {json_mod.dumps({'status': 'retrieving', 'message': '正在检索相关预案...'})}\n\n"
            await asyncio.sleep(0.3)
            yield f"data: {json_mod.dumps({'status': 'generating', 'message': 'AI正在生成应急方案...'})}\n\n"

            result = await generate_plan(None, data.incident, data.matched_plans, data.historical_events)

            async with AsyncSessionLocal() as db:
                r = await db.get(AgentRun, run_id)
                if r:
                    r.output_data = {
                        "plan_content": result["plan_content"],
                        "source_refs": result["source_refs"],
                        "provider": result["provider"],
                    }
                    r.status = "completed"
                    r.finished_at = datetime.now(timezone.utc)
                    await db.commit()

            yield f"data: {json_mod.dumps({'status': 'completed', 'run_id': run_id, 'output_data': {'plan_content': result['plan_content'], 'source_refs': result['source_refs'], 'provider': result['provider']}}, default=str)}\n\n"
        except Exception as e:
            yield f"data: {json_mod.dumps({'status': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/extract")
async def extract_info(data: ExtractRequest):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS["extract"]},
        {"role": "user", "content": f"灾情标题：{data.title}\n灾情描述：{data.description or ''}"},
    ]
    try:
        response = await deepseek_client.chat_completion(messages, max_tokens=1024)
        output = response["choices"][0]["message"]["content"]
        return {"status": "ok", "extracted": output}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/review-plan")
async def review_plan(data: ReviewRequest):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS["review_plan"]},
        {"role": "user", "content": f"请审查以下应急处置方案：\n\n{data.plan_content[:3000]}"},
    ]
    try:
        response = await deepseek_client.chat_completion(messages, max_tokens=2048)
        review = response["choices"][0]["message"]["content"]
        return {"status": "ok", "review": review}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/runs")
async def list_runs(incident_id: Optional[int] = None, limit: int = 20, db: AsyncSession = Depends(get_db)):
    query = select(AgentRun)
    if incident_id:
        query = query.where(AgentRun.incident_id == incident_id)
    query = query.order_by(AgentRun.started_at.desc()).limit(limit)
    result = await db.execute(query)
    runs = result.scalars().all()
    return [_serialize_run(r) for r in runs]


@router.get("/runs/{run_id}")
async def get_run(run_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    citations_result = await db.execute(
        select(Citation).where(Citation.agent_run_id == run_id)
    )
    citations = citations_result.scalars().all()

    data = _serialize_run(run)
    data["citations"] = [
        {"id": c.id, "doc_name": c.doc_name, "chunk_text": (c.chunk_text or "")[:300], "relevance_score": c.relevance_score}
        for c in citations
    ]
    return data
