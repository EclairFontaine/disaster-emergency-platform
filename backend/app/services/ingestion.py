"""采集数据入库管线 - USGS地震+气象写入DB，自动创建灾情"""

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.all import Incident, CollectedEvent
from app.services.collectors.earthquake import EarthquakeCollector
from app.services.collectors.weather import WeatherCollector
from app.services.collectors.warning import WarningCollector


async def ingest_earthquake_events(db: AsyncSession) -> list[int]:
    """USGS 地震 → 自动创建灾情 + 保存事件记录"""
    collector = EarthquakeCollector()
    events = await collector.collect()
    created_ids = []

    for event in events:
        if "error" in event:
            continue
        mag = event.get("magnitude", 0)
        if mag < 1.0:
            continue

        title = event.get("title", f"M{mag}地震")
        lat = event.get("latitude", 0)
        lng = event.get("longitude", 0)

        # 检查去重
        existing = await db.execute(
            select(CollectedEvent).where(
                CollectedEvent.source == "USGS",
                CollectedEvent.external_id == event.get("event_id", ""),
            )
        )
        if existing.scalar_one_or_none():
            continue

        # 保存事件记录
        ce = CollectedEvent(
            source="USGS",
            event_type="earthquake",
            external_id=str(event.get("event_id", "")),
            title=title,
            data=event,
            latitude=lat,
            longitude=lng,
            magnitude=mag,
        )
        db.add(ce)
        await db.flush()

        # M>=3.0 自动创建灾情
        if mag >= 3.0:
            severity = "P1" if mag >= 6.0 else ("P2" if mag >= 5.0 else ("P3" if mag >= 4.0 else "P4"))
            incident = Incident(
                title=title,
                description=f"实时监测：{event.get('place','')} M{mag}级地震，深度{event.get('depth',0)}km",
                category="earthquake",
                severity=severity,
                latitude=lat,
                longitude=lng,
                affected_count=0,
                risk_radius=max(int(mag * 5000), 3000),
                reported_by=1,
                status="pending_review",
                extra_data={"source": "USGS", "event_id": event.get("event_id"), "auto_collected": True},
                created_at=datetime.now(timezone.utc),
            )
            db.add(incident)
            await db.flush()
            await db.refresh(incident)
            ce.created_incident_id = incident.id
            created_ids.append(incident.id)

    await db.flush()
    return created_ids


async def ingest_weather_events(db: AsyncSession) -> list[int]:
    """和风天气数据 → 保存记录 + 极端天气创建灾情"""
    collector = WeatherCollector()
    events = await collector.collect()
    created_ids = []

    for event in events:
        if "error" in event:
            continue
        city = event.get("city", "")
        temp = float(event.get("temperature", 0)) if event.get("temperature") else None
        condition = event.get("condition", "")
        wind = event.get("wind", "") or event.get("wind_speed", "")

        ext_id = f"{event.get('source')}-{city}-{datetime.now(timezone.utc).strftime('%Y%m%d%H')}"
        existing = await db.execute(
            select(CollectedEvent).where(
                CollectedEvent.source == event.get("source", "Weather"),
                CollectedEvent.external_id == ext_id,
            )
        )
        if existing.scalar_one_or_none():
            continue

        ce = CollectedEvent(
            source=event.get("source", "Weather"),
            event_type="weather",
            external_id=ext_id,
            title=f"{city} {temp}C {condition}",
            data=event,
            latitude=event.get("latitude"),
            longitude=event.get("longitude"),
            magnitude=temp,
        )
        db.add(ce)
        await db.flush()

        # 极端天气创建灾情: 暴雨/大风/极端温度
        extreme_keywords = ["暴雨", "暴雪", "台风", "雷暴", "冰雹", "大风", "沙尘"]
        is_extreme = any(kw in condition for kw in extreme_keywords)
        if is_extreme:
            incident = Incident(
                title=f"{city}极端天气预警：{condition}",
                description=f"实时气象监测：{city}当前{condition}，温度{temp}C",
                category="other",
                severity="P3",
                latitude=event.get("latitude") or 25.04,
                longitude=event.get("longitude") or 102.68,
                affected_count=0,
                risk_radius=10000,
                reported_by=1,
                status="pending_review",
                extra_data={"source": event.get("source"), "auto_collected": True},
            )
            db.add(incident)
            await db.flush()
            await db.refresh(incident)
            ce.created_incident_id = incident.id
            created_ids.append(incident.id)

    await db.flush()
    return created_ids


async def run_ingestion(db: AsyncSession) -> dict:
    result = {"earthquake": [], "weather": []}
    try:
        result["earthquake"] = await ingest_earthquake_events(db)
    except Exception as e:
        result["earthquake_error"] = str(e)
    try:
        result["weather"] = await ingest_weather_events(db)
    except Exception as e:
        result["weather_error"] = str(e)
    return result


async def get_latest_events(db: AsyncSession, limit: int = 20):
    result = await db.execute(
        select(CollectedEvent).order_by(CollectedEvent.collected_at.desc()).limit(limit)
    )
    return result.scalars().all()
