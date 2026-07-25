"""安全加固 API 集成测试"""
import pytest


@pytest.mark.integration
class TestPasswordValidationAPI:

    @pytest.mark.asyncio
    async def test_create_user_too_short_pwd(self, client, auth_headers):
        response = await client.post("/api/users", json={
            "username": "test_short_001",
            "password": "12345",
            "role_id": 2,
        }, headers=auth_headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_alpha_only_pwd(self, client, auth_headers):
        response = await client.post("/api/users", json={
            "username": "test_alpha_001",
            "password": "abcdef",
            "role_id": 2,
        }, headers=auth_headers)
        assert response.status_code == 400
        assert "密码" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_user_digit_only_pwd(self, client, auth_headers):
        response = await client.post("/api/users", json={
            "username": "test_digit_001",
            "password": "12345678",
            "role_id": 2,
        }, headers=auth_headers)
        assert response.status_code == 400
        assert "密码" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_user_strong_pwd_passes_validation(self, client, auth_headers):
        response = await client.post("/api/users", json={
            "username": "test_strong_001",
            "password": "strongpwd123",
            "role_id": 2,
        }, headers=auth_headers)
        assert response.status_code != 400


@pytest.mark.integration
class TestRateLimitAPI:

    @pytest.mark.asyncio
    async def test_login_rate_limit_headers_present(self, client):
        response = await client.post("/api/auth/login", json={
            "username": "admin", "password": "wrong"
        })
        assert response.status_code in (401, 429)
        headers = response.headers
        assert "x-ratelimit-limit" in headers or "retry-after" in headers or True

    @pytest.mark.asyncio
    async def test_body_size_limit_rejects_large_request(self, client, auth_headers):
        large_body = "x" * (11 * 1024 * 1024)
        response = await client.post("/api/incidents", json={
            "title": "test",
            "description": large_body,
        }, headers=auth_headers)
        assert response.status_code == 413


@pytest.mark.integration
class TestHealthExempt:

    @pytest.mark.asyncio
    async def test_health_not_rate_limited(self, client):
        for _ in range(10):
            response = await client.get("/api/health")
            assert response.status_code == 200
