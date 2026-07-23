from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.core.database import get_db, AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user, require_admin
from app.models.all import User, CollectedEvent
from app.services.collector import collect_all, collect_earthquake, collect_weather, collect_warnings, get_cached_data
from app.services.ingestion import run_ingestion, get_latest_events
from sqlalchemy import select

router = APIRouter(prefix="/api/collector", tags=["数据采集"])


@router.post("/run")
async def run_all_collectors(user: User = Depends(get_current_user)):
    results = await collect_all()
    return {"status": "ok", "results": results}


@router.post("/run/earthquake")
async def run_earthquake(user: User = Depends(get_current_user)):
    data = await collect_earthquake()
    return {"status": "ok", "count": len(data), "data": data[:10]}


@router.post("/run/weather")
async def run_weather(user: User = Depends(get_current_user)):
    data = await collect_weather()
    return {"status": "ok", "count": len(data), "data": data}


@router.post("/run/warning")
async def run_warning(user: User = Depends(get_current_user)):
    data = await collect_warnings()
    return {"status": "ok", "count": len(data), "data": data[:10]}


@router.get("/data")
async def get_collected_data(user: User = Depends(get_current_user)):
    return get_cached_data()


@router.get("/status")
async def get_collector_status(user: User = Depends(get_current_user)):
    from app.core.config import settings
    cached = get_cached_data()
    return {
        "earthquake": {
            "name": "USGS 全球地震监测",
            "count": len((cached.get("earthquake", {}) or {}).get("data", [])),
            "last_fetch": (cached.get("earthquake", {}) or {}).get("time"),
            "configured": True,
            "status": "active",
        },
        "weather": {
            "name": "气象数据",
            "sources": {
                "openweather": {"name": "OpenWeatherMap", "configured": bool(settings.OPENWEATHER_API_KEY)},
                "qweather": {"name": "和风天气", "configured": bool(settings.QWEATHER_API_KEY)},
            },
            "count": len((cached.get("weather", {}) or {}).get("data", [])),
            "last_fetch": (cached.get("weather", {}) or {}).get("time"),
        },
        "warning": {
            "name": "国家突发事件预警",
            "count": len((cached.get("warning", {}) or {}).get("data", [])),
            "last_fetch": (cached.get("warning", {}) or {}).get("time"),
            "configured": True,
            "status": "active",
        },
    }


@router.post("/ingest")
async def ingest_collected_data(user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as db:
        from app.services.ingestion import ingest_earthquake_events
        eq = await ingest_earthquake_events(db)
        await db.commit()
    return {"status": "ok", "incidents": eq}


@router.post("/ingest/weather")
async def ingest_weather_data(user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as db:
        from app.services.ingestion import ingest_weather_events
        wx = await ingest_weather_events(db)
        await db.commit()
    return {"status": "ok", "incidents": wx}


@router.post("/seed-historical")
async def seed_historical(user: User = Depends(require_admin)):
    """补充云南历史真实灾害数据集"""
    async with AsyncSessionLocal() as db:
        from app.services.historical_seed import seed_historical_events
        result = await seed_historical_events(db)
        await db.commit()
    return {"status": "ok", "added_events": result["events"], "added_incidents": result["incidents"]}


@router.get("/events")
async def list_persisted_events(
    limit: int = Query(50),
    source: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    events = await get_latest_events(db, limit)
    return [
        {"id":e.id,"source":e.source,"event_type":e.event_type,"title":e.title,
         "magnitude":e.magnitude,"latitude":e.latitude,"longitude":e.longitude,
         "image_url":(e.data or {}).get("image_url","") if e.data else "",
         "created_incident_id":e.created_incident_id,
         "collected_at":e.collected_at.isoformat() if e.collected_at else None}
        for e in events
    ]
