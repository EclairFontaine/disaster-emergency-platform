from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user, require_admin, hash_password
from app.models.all import User, Role
from app.schemas.all import UserCreate, UserResponse, UserUpdate, RoleResponse
from app.services.audit import log_action

router = APIRouter(prefix="/api/users", tags=["用户管理"])


@router.get("", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    result = await db.execute(
        select(User).options(selectinload(User.role)).order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    response = []
    for u in users:
        role_data = RoleResponse.model_validate(u.role) if u.role else None
        response.append(UserResponse(
            id=u.id, username=u.username, real_name=u.real_name, phone=u.phone,
            role_id=u.role_id, role=role_data, is_active=u.is_active, created_at=u.created_at,
        ))
    return response


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    new_user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        real_name=data.real_name,
        phone=data.phone,
        role_id=data.role_id,
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)
    await log_action(db, user.id, "create", "user", new_user.id)

    role_data = RoleResponse.model_validate(new_user.role) if new_user.role else None
    return UserResponse(
        id=new_user.id, username=new_user.username, real_name=new_user.real_name,
        phone=new_user.phone, role_id=new_user.role_id, role=role_data,
        is_active=new_user.is_active, created_at=new_user.created_at,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    result = await db.execute(select(User).options(selectinload(User.role)).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")
    role_data = RoleResponse.model_validate(u.role) if u.role else None
    return UserResponse(
        id=u.id, username=u.username, real_name=u.real_name, phone=u.phone,
        role_id=u.role_id, role=role_data, is_active=u.is_active, created_at=u.created_at,
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    result = await db.execute(select(User).options(selectinload(User.role)).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")

    update_data = data.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = hash_password(update_data.pop("password"))
    for key, value in update_data.items():
        setattr(u, key, value)

    await db.flush()
    await db.refresh(u)
    await log_action(db, user.id, "update", "user", user_id)
    role_data = RoleResponse.model_validate(u.role) if u.role else None
    return UserResponse(
        id=u.id, username=u.username, real_name=u.real_name, phone=u.phone,
        role_id=u.role_id, role=role_data, is_active=u.is_active, created_at=u.created_at,
    )


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    result = await db.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")
    if u.username == "admin":
        raise HTTPException(status_code=400, detail="不能删除管理员账号")
    await db.delete(u)
    await db.flush()
