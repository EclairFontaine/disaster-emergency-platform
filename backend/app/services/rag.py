import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.all import EmergencyPlan


async def search_plans(db: AsyncSession, query_text: str) -> list:
    keywords = query_text.split()
    conditions = []
    for kw in keywords[:5]:
        conditions.append(EmergencyPlan.content.ilike(f"%{kw}%"))
        conditions.append(EmergencyPlan.title.ilike(f"%{kw}%"))

    from sqlalchemy import or_
    result = await db.execute(
        select(EmergencyPlan).where(or_(*conditions)).limit(10)
    )
    return result.scalars().all()


async def match_plans(db: AsyncSession, keywords: list[str]) -> list:
    conditions = []
    for kw in keywords[:5]:
        conditions.append(EmergencyPlan.content.ilike(f"%{kw}%"))
        conditions.append(EmergencyPlan.title.ilike(f"%{kw}%"))

    from sqlalchemy import or_
    result = await db.execute(
        select(EmergencyPlan).where(or_(*conditions)).limit(3)
    )
    return result.scalars().all()
