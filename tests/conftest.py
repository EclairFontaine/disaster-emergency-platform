"""测试公共配置 — pytest fixtures"""
import os
import sys
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


def check_postgres_available() -> bool:
    """检测PostgreSQL是否可用"""
    try:
        import asyncpg
        import asyncio
        async def _test():
            conn = await asyncpg.connect(
                host="localhost", port=5432, user="postgres",
                password="postgres", database="disaster", timeout=5
            )
            await conn.close()
            return True
        return asyncio.run(_test())
    except Exception:
        return False


PG_AVAILABLE = check_postgres_available()


@pytest_asyncio.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_app():
    """创建FastAPI测试应用（跳过lifespan，避免后台任务干扰测试）"""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from app.core.config import settings

    app = FastAPI(title=settings.APP_NAME, version="1.0.0", redirect_slashes=False)
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

    return app


@pytest_asyncio.fixture
async def client(test_app):
    """AsyncClient用于发送测试请求"""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def admin_token():
    """admin用户JWT token"""
    from app.core.security import create_access_token
    return create_access_token(data={"sub": "1", "username": "admin"})


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


def pytest_configure(config):
    config.addinivalue_line("markers", "unit: 单元测试（不依赖外部服务，可独立运行）")
    config.addinivalue_line("markers", "integration: 集成测试（需要PostgreSQL + 运行中的后端服务）")
    config.addinivalue_line("markers", "api: API端点测试（需要完整后端运行环境）")
    config.addinivalue_line("markers", "ai: AI相关测试（需要DeepSeek API Key）")
    config.addinivalue_line("markers", "slow: 耗时测试")


def pytest_collection_modifyitems(config, items):
    """当PostgreSQL不可用时自动跳过集成测试"""
    if not PG_AVAILABLE:
        skip_msg = "PostgreSQL不可用，跳过集成测试。"
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(pytest.mark.skip(reason=skip_msg))
