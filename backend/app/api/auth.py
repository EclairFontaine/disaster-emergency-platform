from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.models.all import User, Role
from app.schemas.all import LoginRequest, TokenResponse, UserResponse, RoleResponse
from app.services.audit import log_action

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.username == req.username)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已禁用")

    token = create_access_token(data={"sub": str(user.id), "username": user.username})

    role_data = None
    if user.role:
        role_data = RoleResponse.model_validate(user.role)

    user_data = UserResponse(
        id=user.id,
        username=user.username,
        real_name=user.real_name,
        phone=user.phone,
        role_id=user.role_id,
        role=role_data,
        is_active=user.is_active,
        created_at=user.created_at,
    )

    await log_action(db, user.id, "login", "user", user.id, ip_address="")

    return TokenResponse(access_token=token, token_type="bearer", user=user_data)


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).options(selectinload(User.role)).where(User.id == user.id))
    user = result.scalar_one_or_none()

    role_data = None
    if user.role:
        role_data = RoleResponse.model_validate(user.role)

    return UserResponse(
        id=user.id,
        username=user.username,
        real_name=user.real_name,
        phone=user.phone,
        role_id=user.role_id,
        role=role_data,
        is_active=user.is_active,
        created_at=user.created_at,
    )
