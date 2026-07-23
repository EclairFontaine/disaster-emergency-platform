from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.all import DataSource, User
from app.schemas.all import DataSourceCreate, DataSourceResponse, DataSourceUpdate
from app.services.audit import log_action

router = APIRouter(prefix="/api/datasources", tags=["数据源管理"])


@router.get("", response_model=List[DataSourceResponse])
async def list_datasources(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    result = await db.execute(select(DataSource).order_by(DataSource.name))
    return [DataSourceResponse.model_validate(d) for d in result.scalars().all()]


@router.post("", response_model=DataSourceResponse, status_code=201)
async def create_datasource(
    data: DataSourceCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    ds = DataSource(**data.model_dump())
    db.add(ds)
    await db.flush()
    await db.refresh(ds)
    await log_action(db, user.id, "create", "datasource", ds.id)
    return DataSourceResponse.model_validate(ds)


@router.get("/{ds_id}", response_model=DataSourceResponse)
async def get_datasource(ds_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    result = await db.execute(select(DataSource).where(DataSource.id == ds_id))
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return DataSourceResponse.model_validate(ds)


@router.put("/{ds_id}", response_model=DataSourceResponse)
async def update_datasource(
    ds_id: int,
    data: DataSourceUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    result = await db.execute(select(DataSource).where(DataSource.id == ds_id))
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ds, key, value)
    await db.flush()
    await db.refresh(ds)
    return DataSourceResponse.model_validate(ds)


@router.delete("/{ds_id}", status_code=204)
async def delete_datasource(ds_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    result = await db.execute(select(DataSource).where(DataSource.id == ds_id))
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")
    await db.delete(ds)
    await db.flush()
