"""API端点测试 — 需要PostgreSQL运行环境"""
import pytest


@pytest.mark.integration
class TestHealth:
    """健康检查（无DB依赖，可直接测试）"""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


@pytest.mark.integration
class TestAuth:
    """认证接口"""

    @pytest.mark.asyncio
    async def test_login_success(self, client, db_session):
        from app.core.security import hash_password
        from app.models.all import Role, User
        role = Role(name="admin", description="管理员")
        db_session.add(role)
        await db_session.flush()
        user = User(username="testadmin", password_hash=hash_password("admin123"), real_name="测试", role_id=role.id)
        db_session.add(user)
        await db_session.flush()
        await db_session.commit()

        response = await client.post("/api/auth/login", json={"username": "testadmin", "password": "admin123"})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, db_session):
        from app.core.security import hash_password
        from app.models.all import Role, User
        role = Role(name="admin", description="管理员")
        db_session.add(role)
        await db_session.flush()
        user = User(username="testadmin2", password_hash=hash_password("correct"), real_name="测试", role_id=role.id)
        db_session.add(user)
        await db_session.flush()
        await db_session.commit()

        response = await client.post("/api/auth/login", json={"username": "testadmin2", "password": "wrong"})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_no_user(self, client):
        response = await client.post("/api/auth/login", json={"username": "nobody", "password": "x"})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_unauthorized(self, client):
        response = await client.get("/api/auth/me")
        assert response.status_code in (401, 403)


@pytest.mark.integration
class TestIncidentsAPI:
    """灾情管理接口"""

    @pytest.mark.asyncio
    async def test_list_empty(self, client, auth_headers):
        response = await client.get("/api/incidents", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_create_requires_auth(self, client):
        response = await client.post("/api/incidents", json={"title": "test"})
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, client, auth_headers):
        response = await client.get("/api/incidents/99999", headers=auth_headers)
        assert response.status_code == 404


@pytest.mark.integration
class TestResourcesAPI:
    """资源管理接口"""

    @pytest.mark.asyncio
    async def test_list_empty(self, client, auth_headers):
        response = await client.get("/api/resources", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.integration
class TestStatisticsAPI:
    """统计接口"""

    @pytest.mark.asyncio
    async def test_get_statistics(self, client, auth_headers):
        response = await client.get("/api/statistics", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_incidents" in data
        assert "total_resources" in data
