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


@router.post("/ingest")
async def ingest_collected_data(user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as db:
        result = await run_ingestion(db)
    return {"status": "ok", "created_incidents": result["earthquake"]}
