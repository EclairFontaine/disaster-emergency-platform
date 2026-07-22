"""AI 方案生成引擎 - DeepSeek优先，模板兜底"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.all import Incident, EmergencyPlan, AgentRun, Citation
from app.services.rag import search_plans
from datetime import datetime, timezone


async def generate_plan_with_ai(db: AsyncSession, incident: Incident, agent_run: AgentRun) -> str:
    """优先尝试 DeepSeek，失败则用模板生成"""
    try:
        from app.services.deepseek import deepseek_client, SYSTEM_PROMPTS

        plans = await search_plans(db, f"{incident.title or ''} {incident.description or ''} {incident.category or ''}")
        plan_texts = []
        citations_data = []
        for i, p in enumerate(plans[:3]):
            snippet = (p.content or "")[:500]
            plan_texts.append(f"参考预案{i+1}：{snippet}")
            citations_data.append({"plan_id": p.id, "doc_name": p.title, "chunk_text": snippet, "score": 1.0 - i * 0.1})

        ref_text = "\n\n".join(plan_texts) if plan_texts else "暂无匹配参考预案"
        messages = [
            {"role": "system", "content": SYSTEM_PROMPTS["generate"]},
            {"role": "user", "content": f"灾情信息：\n标题：{incident.title}\n类型：{incident.category or '未知'}\n严重程度：{incident.severity}\n描述：{incident.description or ''}\n影响人数：{incident.affected_count or '未知'}\n位置：({incident.latitude}, {incident.longitude})\n\n参考预案：\n{ref_text}"},
        ]
        response = await deepseek_client.chat_completion(messages, max_tokens=4096)
        plan_content = response["choices"][0]["message"]["content"]

        for cit in citations_data:
            db.add(Citation(
                agent_run_id=agent_run.id,
                doc_name=cit["doc_name"],
                chunk_text=cit["chunk_text"][:1000],
                relevance_score=cit["score"],
            ))

        return plan_content, [{"doc_name": c["doc_name"], "chunk_text": c["chunk_text"][:200], "score": c["score"]} for c in citations_data]

    except Exception:
        pass

    # DeepSeek 失败 → 使用模板引擎本地生成
    return await generate_plan_with_template(db, incident, agent_run)


async def generate_plan_with_template(db: AsyncSession, incident: Incident, agent_run: AgentRun) -> tuple:
    """本地模板引擎 - 基于匹配预案组装方案，无需AI"""

    plans = await search_plans(db, f"{incident.title or ''} {incident.description or ''} {incident.category or ''}")

    cat_labels = {"earthquake":"地震灾害","flood":"洪涝灾害","landslide":"地质灾害","fire":"森林火灾","other":"自然灾害"}
    sev_labels = {"P1":"特别重大(I级)","P2":"重大(II级)","P3":"较大(III级)","P4":"一般(IV级)"}
    cat = cat_labels.get(incident.category or "other", "自然灾害")
    sev = sev_labels.get(incident.severity, "一般")

    plan_parts = [
        f"# {incident.title} — 应急处置方案",
        "",
        f"**生成时间**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**生成方式**: 本地模板引擎 (DeepSeek未配置时自动降级)",
        f"**灾情类型**: {cat} | **严重程度**: {sev}",
        "",
        "---",
        "",
        "## 一、灾情概述",
        f"- **标题**: {incident.title}",
        f"- **类型**: {cat}",
        f"- **严重程度**: {sev}",
        f"- **位置**: 经纬度({incident.latitude}, {incident.longitude})",
        f"- **影响人数**: {incident.affected_count or '待评估'}人",
        f"- **灾情描述**: {incident.description or '待补充'}",
        "",
        "## 二、应急响应等级",
        f"根据灾情类型及严重程度，建议启动**{sev}应急响应**。",
        "立即成立应急指挥部，集结专业救援力量，统筹协调各方资源开展救援工作。",
        "",
        "## 三、组织机构与职责",
        "1. **综合协调组**: 负责指挥调度、信息汇总、指令传达",
        "2. **抢险救援组**: 组织救援队伍第一时间赴灾区开展生命搜救",
        "3. **医疗救治组**: 设立临时医疗点，开展伤员救治和卫生防疫",
        "4. **群众安置组**: 设置临时避难场所，保障受灾群众基本生活",
        "5. **交通保障组**: 抢通受损道路，保障救援通道畅通",
        "6. **物资保障组**: 调拨救灾物资，确保物资及时到位",
        "7. **通信保障组**: 抢修通信设施，保障指挥通信畅通",
        "8. **次生灾害防控组**: 监测防控滑坡、泥石流、堰塞湖等次生灾害",
        "9. **信息发布组**: 及时准确发布灾情和救援进展信息",
        "",
        "## 四、处置措施",
        "### 第一阶段：应急响应（0-24小时）",
        "- 立即启动应急响应机制，发布预警信息",
        "- 组织危险区域群众紧急转移避险",
        "- 集结消防救援、武警、医疗等专业力量",
        "- 启动应急通信系统，建立前线指挥部",
        "- 开展灾情初步评估，确定救援重点区域",
        "",
        "### 第二阶段：紧急救援（24-72小时）",
        "- 全力开展生命搜救工作，72小时黄金救援期内最大限度减少伤亡",
        "- 设立临时医疗点，开展伤员分类救治和转运",
        "- 抢通受损的道路、电力、通信、供水等基础设施",
        "- 设立临时安置点，发放食品、饮用水、帐篷、棉被等救灾物资",
        "- 开展次生灾害隐患排查和监测预警",
        "",
        "### 第三阶段：过渡安置（72小时-14天）",
        "- 组织灾情详细评估，统计灾害损失",
        "- 做好受灾群众过渡性安置和生活保障",
        "- 开展环境消杀和饮用水安全检测，严防疫情",
        "- 恢复受损基础设施，保障基本生产和生活",
        "- 组织专业力量开展灾后恢复重建规划",
        "",
        "### 第四阶段：恢复重建",
        "- 编制灾后恢复重建规划方案",
        "- 启动受损房屋和基础设施修缮重建",
        "- 组织开展受灾群众生产自救和心理疏导",
        "- 总结应急处置经验，完善应急预案",
    ]

    citations_data = []
    if plans:
        plan_parts.append("")
        plan_parts.append("## 五、参考预案")
        for i, p in enumerate(plans[:3]):
            snippet = (p.content or "")[:300]
            plan_parts.append(f"")
            plan_parts.append(f"### 参考预案{i+1}：《{p.title}》")
            plan_parts.append(f"")
            plan_parts.append(snippet + ("..." if len(p.content or "") > 300 else ""))
            citations_data.append({"plan_id": p.id, "doc_name": p.title, "chunk_text": snippet, "score": 1.0 - i * 0.1})

            db.add(Citation(
                agent_run_id=agent_run.id,
                doc_name=p.title,
                chunk_text=snippet,
                relevance_score=1.0 - i * 0.1,
            ))

    plan_parts.append("")
    plan_parts.append("---")
    plan_parts.append(f"*本方案由AI应急辅助系统自动生成（{'DeepSeek AI' if False else '本地模板引擎'}），请指挥人员审核后执行。*")

    plan_content = "\n".join(plan_parts)
    source_refs = [{"doc_name": c["doc_name"], "chunk_text": c["chunk_text"][:200], "score": c["score"]} for c in citations_data]

    return plan_content, source_refs
