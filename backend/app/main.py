from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
from app.core.milvus import connect_milvus, disconnect_milvus, create_plan_chunks_collection
from app.core.security import hash_password
from app.models.all import Role, User
from sqlalchemy import select


async def scheduled_ingestion():
    while True:
        try:
            async with AsyncSessionLocal() as db:
                from app.services.ingestion import run_ingestion
                result = await run_ingestion(db)
                if result.get("earthquake"):
                    print(f"[Scheduler] 采集完成, 新灾情: {result['earthquake']}")
        except Exception as e:
            print(f"[Scheduler] 采集异常: {e}")
        await asyncio.sleep(1800)  # 30 minutes



@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_data()
    try:
        create_plan_chunks_collection()
        await connect_milvus()
    except Exception:
        pass

    # Start background scheduler for data collection
    scheduler_task = asyncio.create_task(scheduled_ingestion())

    # Run initial ingestion to get real-time earthquake data
    try:
        async with AsyncSessionLocal() as db:
            from app.services.ingestion import run_ingestion
            result = await run_ingestion(db)
            if result.get("earthquake"):
                print(f"[Startup] 初始化实时地震数据: {result['earthquake']}")
    except Exception:
        pass

    yield

    scheduler_task.cancel()
    try:
        await disconnect_milvus()
    except Exception:
        pass


async def seed_data():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Role))
        existing_roles = result.scalars().all()
        if not existing_roles:
            roles = [
                Role(name="admin", description="系统管理员"),
                Role(name="info_reporter", description="普通信息员，上报灾情"),
                Role(name="emergency_commander", description="应急指挥人员，审核事件、生成处置方案"),
                Role(name="resource_manager", description="资源管理员，维护人员、车辆、物资和避难场所"),
            ]
            db.add_all(roles)
            await db.flush()

        result2 = await db.execute(select(User).where(User.username == "admin"))
        if not result2.scalar_one_or_none():
            role_result = await db.execute(select(Role).where(Role.name == "admin"))
            admin_role = role_result.scalar_one()
            admin_user = User(
                username="admin",
                password_hash=hash_password("admin123"),
                real_name="系统管理员",
                role_id=admin_role.id,
            )
            db.add(admin_user)
            await db.flush()

        # Seed demo users
        demo_users = [
            ("reporter1", "info_reporter", "信息员张三"),
            ("commander1", "emergency_commander", "指挥员李四"),
            ("resource1", "resource_manager", "资源管理员工五"),
        ]
        for uname, rname, real_name in demo_users:
            u = await db.execute(select(User).where(User.username == uname))
            if not u.scalar_one_or_none():
                r = await db.execute(select(Role).where(Role.name == rname))
                role = r.scalar_one()
                db.add(User(username=uname, password_hash=hash_password("123456"), real_name=real_name, role_id=role.id))
        await db.flush()
        await db.commit()

    # Seed demo data (plans, resources, datasources, incidents)
    try:
        async with AsyncSessionLocal() as db:
            from app.services.seed_data import seed_demo_data
            await seed_demo_data(db)
    except Exception:
        pass


app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan, redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import auth, incidents, resources, plans, agent, datasources, users, websocket, audit, statistics, collector

app.include_router(auth.router)
app.include_router(incidents.router)
app.include_router(resources.router)
app.include_router(plans.router)
app.include_router(agent.router)
app.include_router(datasources.router)
app.include_router(users.router)
app.include_router(websocket.router)
app.include_router(audit.router)
app.include_router(statistics.router)
app.include_router(collector.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "name": settings.APP_NAME}
