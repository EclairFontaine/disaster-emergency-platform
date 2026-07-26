"""3级降级方案生成引擎: Dify RAG → DeepSeek+RAG → 模板兜底"""

from datetime import datetime, timezone
from typing import Optional

from config import settings
from clients.deepseek import deepseek_client, SYSTEM_PROMPTS
from clients.dify import dify_client


async def generate_plan(
    incident: dict,
    matched_plans: list[dict],
    historical_events: list[dict],
) -> dict:
    """主入口: 3级降级方案生成, 返回 {plan_content, source_refs, citations, provider}"""

    # Tier 1: Dify RAG
    if settings.DIFY_API_KEY and settings.DIFY_API_KEY not in ("app-placeholder", "", None):
        result = await _try_dify(incident)
        if result:
            return result

    # Tier 2: DeepSeek + RAG context
    try:
        result = await _try_deepseek(incident, matched_plans, historical_events)
        if result:
            return result
    except Exception:
        pass

    # Tier 3: Template engine
    return await _template_fallback(incident, matched_plans, historical_events)


async def _try_dify(incident: dict) -> dict | None:
    try:
        query = f"{incident.get('title', '')} {incident.get('description', '')}"
        inputs = {
            "incident_title": incident.get("title", ""),
            "incident_category": incident.get("category", "unknown"),
            "incident_severity": incident.get("severity", ""),
            "incident_description": incident.get("description", ""),
            "incident_latitude": str(incident.get("latitude", "")),
            "incident_longitude": str(incident.get("longitude", "")),
            "affected_count": str(incident.get("affected_count", "")),
        }

        response = await dify_client.chat_blocking(query=query, inputs=inputs)
        answer = response.get("answer", "")

        metadata = response.get("metadata", {}) or {}
        retriever_resources = metadata.get("retriever_resources", [])

        citations_data = []
        for i, resource in enumerate(retriever_resources):
            doc_name = resource.get("document_name", f"知识库文档{i+1}")
            chunk_text = (resource.get("content", "") or "")[:1000]
            score = resource.get("score", 1.0 - i * 0.1)
            citations_data.append({
                "doc_name": doc_name,
                "chunk_text": chunk_text[:300],
                "score": score,
            })

        return {
            "plan_content": answer,
            "source_refs": citations_data,
            "citations": citations_data,
            "provider": "dify",
        }
    except Exception:
        return None


async def _try_deepseek(incident: dict, matched_plans: list[dict], historical_events: list[dict]) -> dict | None:
    plan_texts = []
    citations_data = []
    for i, p in enumerate(matched_plans[:3]):
        snippet = (p.get("content", "") or "")[:500]
        plan_texts.append(f"参考预案{i+1}《{p.get('title', '无标题')}》：{snippet}")
        citations_data.append({
            "doc_name": p.get("title", "预案"),
            "chunk_text": snippet,
            "score": 1.0 - i * 0.1,
        })

    hist_text = ""
    if historical_events:
        lines = ["近期周边真实灾害事件："]
        for i, he in enumerate(historical_events[:5]):
            lines.append(
                f"  {i+1}. {he.get('title', '')} | 距离: {he.get('distance_km', '?')}km | "
                f"坐标: ({he.get('latitude', '?')}, {he.get('longitude', '?')}) | 时间: {he.get('time', '?')[:10]}"
            )
            citations_data.append({
                "doc_name": f"历史事件: {he.get('title', '')}",
                "chunk_text": f"距离{he.get('distance_km', '?')}km, {he.get('time', '?')[:10]}",
                "score": 1.0 - i * 0.15,
            })
        hist_text = "\n".join(lines)

    ref_text = "\n\n".join(plan_texts) if plan_texts else "暂无匹配参考预案"
    rag_context = f"{ref_text}\n\n{hist_text}" if hist_text else ref_text

    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS["generate_plan"]},
        {"role": "user", "content": (
            f"灾情信息：\n标题：{incident.get('title', '')}\n类型：{incident.get('category', '未知')}\n"
            f"严重程度：{incident.get('severity', '')}\n描述：{incident.get('description', '')}\n"
            f"影响人数：{incident.get('affected_count', '未知')}\n"
            f"位置：({incident.get('latitude', '')}, {incident.get('longitude', '')})\n\n"
            f"参考预案+历史数据：\n{rag_context}"
        )},
    ]
    response = await deepseek_client.chat_completion(messages, max_tokens=4096)
    plan_content = response["choices"][0]["message"]["content"]

    return {
        "plan_content": plan_content,
        "source_refs": [{"doc_name": c["doc_name"], "chunk_text": c["chunk_text"][:200], "score": c["score"]} for c in citations_data],
        "citations": citations_data,
        "provider": "deepseek",
    }


async def _template_fallback(incident: dict, matched_plans: list[dict], historical_events: list[dict]) -> dict:
    cat_labels = {"earthquake": "地震灾害", "flood": "洪涝灾害", "landslide": "地质灾害", "fire": "森林火灾", "other": "自然灾害"}
    sev_labels = {"P1": "特别重大(I级)", "P2": "重大(II级)", "P3": "较大(III级)", "P4": "一般(IV级)"}
    cat = cat_labels.get(incident.get("category", "other"), "自然灾害")
    sev = sev_labels.get(incident.get("severity", "P3"), "一般")

    plan_parts = [
        f"# {incident.get('title', '未知灾情')} — 应急处置方案",
        "",
        f"**生成时间**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**生成方式**: 本地模板引擎 (AI服务不可用时自动降级)",
        f"**灾情类型**: {cat} | **严重程度**: {sev}",
        "",
        "---",
        "",
        "## 一、灾情概述",
        f"- **标题**: {incident.get('title', '')}",
        f"- **类型**: {cat}",
        f"- **严重程度**: {sev}",
        f"- **位置**: 经纬度({incident.get('latitude', '')}, {incident.get('longitude', '')})",
        f"- **影响人数**: {incident.get('affected_count', '待评估')}人",
        f"- **灾情描述**: {incident.get('description', '待补充')}",
        "",
        "## 二、应急响应等级",
        f"根据灾情类型及严重程度，建议启动**{sev}应急响应**。",
        "立即成立应急指挥部，集结专业救援力量，统筹协调各方资源。",
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
    if matched_plans:
        plan_parts.append("")
        plan_parts.append("## 五、参考预案")
        for i, p in enumerate(matched_plans[:3]):
            snippet = (p.get("content", "") or "")[:300]
            plan_parts.append(f"### 参考预案{i+1}：《{p.get('title', '无标题')}》")
            plan_parts.append(snippet + ("..." if len(p.get("content", "") or "") > 300 else ""))
            citations_data.append({
                "doc_name": p.get("title", "预案"),
                "chunk_text": snippet,
                "score": 1.0 - i * 0.1,
            })

    if historical_events:
        plan_parts.append("")
        plan_parts.append("## 六、周边近期真实灾害事件")
        for i, he in enumerate(historical_events[:5]):
            plan_parts.append(f"- {he.get('title', '')} | 距离约{he.get('distance_km', '?')}km | {he.get('time', '?')[:10]}")
            citations_data.append({
                "doc_name": f"历史: {he.get('title', '')}",
                "chunk_text": f"距离{he.get('distance_km', '?')}km, {he.get('time', '?')[:10]}",
                "score": 1.0 - i * 0.1,
            })

    plan_parts.append("")
    plan_parts.append("---")
    plan_parts.append("*本方案由AI应急辅助系统生成，请指挥人员审核后执行。*")

    plan_content = "\n".join(plan_parts)

    return {
        "plan_content": plan_content,
        "source_refs": [{"doc_name": c["doc_name"], "chunk_text": c["chunk_text"][:200], "score": c["score"]} for c in citations_data],
        "citations": citations_data,
        "provider": "template",
    }
