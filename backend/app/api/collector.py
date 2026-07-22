from fastapi import APIRouter, Depends
from app.core.database import get_db, AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user, require_admin
from app.models.all import User
from app.services.collector import collect_all, collect_earthquake, collect_weather, collect_warnings, get_cached_data
from app.services.ingestion import run_ingestion

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
        result = await run_ingestion(db)
    return {"status": "ok", "created_incidents": result["earthquake"]}
