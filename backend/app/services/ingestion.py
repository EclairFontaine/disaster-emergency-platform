"""采集数据入写入灾情库 - 将 USGS/气象/预警数据自动转为灾情工单"""

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.all import Incident
from app.services.collectors.earthquake import EarthquakeCollector
from app.services.collectors.weather import WeatherCollector


async def ingest_earthquake_events(db: AsyncSession) -> list[int]:
    """从 USGS 采集地震数据并自动创建灾情工单"""
    collector = EarthquakeCollector()
    events = await collector.collect()
    created_ids = []

    for event in events:
        if "error" in event:
            continue
        mag = event.get("magnitude", 0)
        if mag < 3.0:  # 低于3级不自动创建
            continue

        # 检查是否已存在同样的灾情
        title = event.get("title", f"M{mag}地震")
        lat = event.get("latitude", 0)
        lng = event.get("longitude", 0)

        existing = await db.execute(
            select(Incident).where(
                Incident.title == title,
                Incident.latitude == lat,
                Incident.longitude == lng,
            )
        )
        if existing.scalar_one_or_none():
            continue

        # 根据震级确定严重程度
        if mag >= 6.0:
            severity = "P1"
        elif mag >= 5.0:
            severity = "P2"
        elif mag >= 4.0:
            severity = "P3"
        else:
            severity = "P4"

        incident = Incident(
            title=title,
            description=f"USGS实时监测：{event.get('place','')} M{mag}级地震，深度{event.get('depth',0)}km",
            category="earthquake",
            severity=severity,
            latitude=lat,
            longitude=lng,
            affected_count=0,
            risk_radius=max(int(mag * 5000), 3000),
            reported_by=1,  # system
            status="pending_review",
            extra_data={"source": "USGS", "event_id": event.get("event_id"), "fetch_time": event.get("fetch_time")},
            created_at=datetime.now(timezone.utc),
        )
        db.add(incident)
        await db.flush()
        await db.refresh(incident)
        created_ids.append(incident.id)

    await db.commit()
    return created_ids


async def run_ingestion(db: AsyncSession) -> dict:
    """运行所有采集管道"""
    result = {"earthquake": [], "weather": []}

    try:
        result["earthquake"] = await ingest_earthquake_events(db)
    except Exception as e:
        result["earthquake"] = {"error": str(e)}

    return result
