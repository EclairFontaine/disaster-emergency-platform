"""AI 方案生成后自动匹配资源并创建调度单"""

import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.all import Resource, DispatchOrder, Incident


def haversine(lat1, lng1, lat2, lng2):
    if not all([lat1, lng1, lat2, lng2]):
        return float("inf")
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# 根据灾情类型推荐资源配比
RESOURCE_TEMPLATES = {
    "earthquake": [
        {"type": "personnel", "qty_ratio": 0.3, "name_hint": "救援队"},
        {"type": "vehicle", "qty_ratio": 0.2, "name_hint": "急救"},
        {"type": "material", "qty_ratio": 0.3, "name_hint": "帐篷"},
        {"type": "shelter", "qty_ratio": 0.1, "name_hint": "避难"},
    ],
    "landslide": [
        {"type": "personnel", "qty_ratio": 0.4, "name_hint": "救援"},
        {"type": "vehicle", "qty_ratio": 0.3, "name_hint": "工程"},
        {"type": "material", "qty_ratio": 0.2, "name_hint": "食品"},
        {"type": "shelter", "qty_ratio": 0.1, "name_hint": "避难"},
    ],
    "flood": [
        {"type": "personnel", "qty_ratio": 0.3, "name_hint": "救援"},
        {"type": "vehicle", "qty_ratio": 0.2, "name_hint": "救护"},
        {"type": "material", "qty_ratio": 0.4, "name_hint": "饮用水"},
        {"type": "shelter", "qty_ratio": 0.1, "name_hint": "避难"},
    ],
    "fire": [
        {"type": "personnel", "qty_ratio": 0.4, "name_hint": "消防"},
        {"type": "vehicle", "qty_ratio": 0.3, "name_hint": "消防"},
        {"type": "material", "qty_ratio": 0.1, "name_hint": "食品"},
        {"type": "shelter", "qty_ratio": 0.1, "name_hint": "避难"},
    ],
    "other": [
        {"type": "personnel", "qty_ratio": 0.3, "name_hint": "救援"},
        {"type": "vehicle", "qty_ratio": 0.2, "name_hint": "急救"},
        {"type": "material", "qty_ratio": 0.3, "name_hint": "物资"},
        {"type": "shelter", "qty_ratio": 0.1, "name_hint": "避难"},
    ],
}


async def auto_match_and_dispatch(
    db: AsyncSession,
    incident: Incident,
    plan_id: int,
) -> list[dict]:
    """根据灾情自动匹配资源并创建调度单"""
    template = RESOURCE_TEMPLATES.get(incident.category or "other", RESOURCE_TEMPLATES["other"])
    dispatch_results = []

    results = await db.execute(
        select(Resource).where(
            Resource.available_qty > Resource.locked_qty,
            Resource.status == "idle",
        )
    )
    all_resources = results.scalars().all()

    if not all_resources:
        return []

    # 按距离排序
    sorted_resources = sorted(all_resources, key=lambda r: haversine(
        incident.latitude, incident.longitude, r.latitude, r.longitude
    ))

    for rule in template:
        candidates = [r for r in sorted_resources if r.type == rule["type"]]
        if not candidates:
            candidates = [r for r in sorted_resources if rule["name_hint"] in (r.name or "")]
        if not candidates:
            continue

        resource = candidates[0]
        available = resource.available_qty - resource.locked_qty
        if available <= 0:
            continue

        qty = max(1, min(available, int(resource.quantity * rule["qty_ratio"])))
        if qty <= 0:
            qty = 1

        try:
            resource.locked_qty += qty
            order = DispatchOrder(
                incident_id=incident.id,
                plan_id=plan_id,
                resource_id=resource.id,
                quantity=qty,
                dest_latitude=incident.latitude,
                dest_longitude=incident.longitude,
                status="pending",
            )
            db.add(order)
            await db.flush()
            await db.refresh(order)

            dispatch_results.append({
                "dispatch_id": order.id,
                "resource_id": resource.id,
                "resource_name": resource.name,
                "type": resource.type,
                "quantity": qty,
            })
        except Exception:
            pass

    if dispatch_results:
        await db.flush()

    return dispatch_results
