from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.all import AgentRun, Citation, EmergencyPlan
from app.services.deepseek import deepseek_client, SYSTEM_PROMPTS
from app.services.rag import search_plans


async def create_agent_run(db: AsyncSession, incident_id: int, run_type: str, input_data: dict = None) -> AgentRun:
    run = AgentRun(
        incident_id=incident_id,
        run_type=run_type,
        input_data=input_data or {},
        status="running",
    )
    db.add(run)
    await db.flush()
    return run


async def finish_agent_run(db: AsyncSession, run: AgentRun, output_data: dict = None, error: str = None):
    run.finished_at = datetime.now(timezone.utc)
    if error:
        run.status = "failed"
        run.error_message = error
    else:
        run.status = "completed"
        run.output_data = output_data or {}
    await db.flush()


async def run_extraction(db: AsyncSession, incident_id: int) -> AgentRun:
    from app.models.all import Incident
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise ValueError("灾情不存在")

    run = await create_agent_run(db, incident_id, "extract", {"title": incident.title, "description": incident.description})

    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPTS["extract"]},
            {"role": "user", "content": f"灾情标题：{incident.title}\n灾情描述：{incident.description or ''}"},
        ]
        response = await deepseek_client.chat_completion(messages)
        output = response["choices"][0]["message"]["content"]
        output_data = {"extracted_info": output}
        await finish_agent_run(db, run, output_data)

        import json
        try:
            data = json.loads(output)
            if isinstance(data, dict):
                inc_result = await db.execute(select(Incident).where(Incident.id == incident_id))
                inc = inc_result.scalar_one_or_none()
                if inc:
                    current_meta = inc.extra_data or {}
                    current_meta["extracted"] = data
                    inc.extra_data = current_meta
                    await db.flush()
        except (json.JSONDecodeError, ValueError):
            pass

    except Exception as e:
        await finish_agent_run(db, run, error=str(e))

    return run


async def run_plan_generation(db: AsyncSession, incident_id: int) -> AgentRun:
    from app.models.all import Incident
    from app.services.ai_engine import generate_plan_with_ai
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise ValueError("灾情不存在")

    run = await create_agent_run(db, incident_id, "generate")

    try:
        plan_content, source_refs = await generate_plan_with_ai(db, incident, run)

        plan = EmergencyPlan(
            incident_id=incident_id,
            title=f"应急方案-{incident.title}",
            content=plan_content,
            generated_by="ai",
            source_refs=source_refs,
        )
        db.add(plan)
        await db.flush()

        output_data = {"plan_id": plan.id, "plan_content": plan_content, "source_refs": source_refs}

        # 自动匹配资源并创建调度单
        try:
            from app.services.resource_auto_dispatcher import auto_match_and_dispatch
            dispatches = await auto_match_and_dispatch(db, incident, plan.id)
            output_data["auto_dispatches"] = dispatches
        except Exception:
            output_data["auto_dispatches"] = []

        await finish_agent_run(db, run, output_data)

    except Exception as e:
        await finish_agent_run(db, run, error=str(e))

    return run


async def stream_generate_plan(db: AsyncSession, incident_id: int, agent_run_id: int):
    import json as json_mod
    import asyncio
    from app.models.all import Incident
    from app.services.ai_engine import generate_plan_with_ai

    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        yield f"data: {json_mod.dumps({'status': 'error', 'message': '灾情不存在'})}\n\n"
        return

    run_result = await db.execute(select(AgentRun).where(AgentRun.id == agent_run_id))
    run = run_result.scalar_one_or_none()
    if not run:
        yield f"data: {json_mod.dumps({'status': 'error', 'message': 'Agent任务不存在'})}\n\n"
        return

    yield f"data: {json_mod.dumps({'status': 'extracting', 'message': '正在分析灾情信息...'})}\n\n"
    await asyncio.sleep(0.3)
    yield f"data: {json_mod.dumps({'status': 'retrieving', 'message': '正在从知识库检索相关预案...'})}\n\n"
    await asyncio.sleep(0.3)
    yield f"data: {json_mod.dumps({'status': 'generating', 'message': 'AI正在生成应急方案...'})}\n\n"

    try:
        plan_content, source_refs = await generate_plan_with_ai(db, incident, run)

        plan = EmergencyPlan(
            incident_id=incident_id,
            title=f"应急方案-{incident.title}",
            content=plan_content,
            generated_by="ai",
            source_refs=source_refs,
        )
        db.add(plan)
        await db.flush()
        await db.commit()

        output_data = {"plan_id": plan.id, "plan_content": plan_content, "source_refs": source_refs}
        await finish_agent_run(db, run, output_data)

        yield f"data: {json_mod.dumps({'status': 'completed', 'agent_run_id': run.id, 'output_data': output_data})}\n\n"

    except Exception as e:
        await finish_agent_run(db, run, error=str(e))
        yield f"data: {json_mod.dumps({'status': 'error', 'message': str(e)})}\n\n"


async def run_plan_review(db: AsyncSession, plan_id: int) -> AgentRun:
    result = await db.execute(select(EmergencyPlan).where(EmergencyPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise ValueError("预案不存在")

    run = await create_agent_run(db, plan.incident_id or 0, "review", {"plan_id": plan_id, "plan_content": plan.content[:2000]})

    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPTS["review_plan"]},
            {"role": "user", "content": f"请审查以下应急处置方案：\n\n{plan.content}"},
        ]
        response = await deepseek_client.chat_completion(messages)
        review = response["choices"][0]["message"]["content"]
        output_data = {"review": review}
        await finish_agent_run(db, run, output_data)
    except Exception as e:
        await finish_agent_run(db, run, error=str(e))

    return run
