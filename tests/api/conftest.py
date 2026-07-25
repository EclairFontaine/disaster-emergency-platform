"""API集成测试配置 - 使用真实HTTP客户端连接运行中的后端"""
import pytest
import pytest_asyncio
import httpx

BACKEND_URL = "http://127.0.0.1:8000"


@pytest_asyncio.fixture
async def client():
    async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=30) as ac:
        yield ac


@pytest.fixture
def admin_token():
    from app.core.security import create_access_token
    return create_access_token(data={"sub": "1", "username": "admin"})


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
