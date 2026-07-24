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
    """认证接口 — 使用已种子化的用户数据"""

    @pytest.mark.asyncio
    async def test_login_admin_success(self, client):
        """测试种子管理员账号登录"""
        response = await client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "admin"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client):
        """测试错误密码"""
        response = await client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_no_user(self, client):
        """测试不存在的用户"""
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
    async def test_list_incidents(self, client, auth_headers):
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
    async def test_list_resources(self, client, auth_headers):
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
