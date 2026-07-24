"""API集成测试扩展 — plans, agent, collector, datasources, users, audit, websocket"""

import pytest


@pytest.mark.integration
class TestPlansAPI:
    """应急预案接口"""

    @pytest.mark.asyncio
    async def test_list_plans(self, client, auth_headers):
        response = await client.get("/api/plans", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_create_plan(self, client, auth_headers):
        response = await client.post("/api/plans", json={
            "title": "测试预案", "content": "# 测试内容\n这是测试"
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "测试预案"
        assert data["generated_by"] == "manual"

    @pytest.mark.asyncio
    async def test_get_plan_not_found(self, client, auth_headers):
        response = await client.get("/api/plans/99999", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_search_plans(self, client, auth_headers):
        response = await client.post("/api/plans/search", json={"query": "地震"}, headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_update_plan(self, client, auth_headers):
        create_resp = await client.post("/api/plans", json={
            "title": "旧标题", "content": "旧内容"
        }, headers=auth_headers)
        plan_id = create_resp.json()["id"]
        response = await client.put(f"/api/plans/{plan_id}", json={
            "title": "新标题", "content": "新内容"
        }, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["title"] == "新标题"

    @pytest.mark.asyncio
    async def test_delete_plan(self, client, auth_headers):
        create_resp = await client.post("/api/plans", json={
            "title": "待删除", "content": "内容"
        }, headers=auth_headers)
        plan_id = create_resp.json()["id"]
        response = await client.delete(f"/api/plans/{plan_id}", headers=auth_headers)
        assert response.status_code == 204


@pytest.mark.integration
class TestAgentAPI:
    """Agent执行记录接口"""

    @pytest.mark.asyncio
    async def test_list_agent_runs(self, client, auth_headers):
        response = await client.get("/api/agent/runs", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_agent_run_not_found(self, client, auth_headers):
        response = await client.get("/api/agent/runs/99999", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_retry_not_failed(self, client, auth_headers):
        response = await client.post("/api/agent/runs/1/retry", headers=auth_headers)
        assert response.status_code in (400, 404)


@pytest.mark.integration
class TestCollectorAPI:
    """数据采集接口"""

    @pytest.mark.asyncio
    async def test_get_collector_status(self, client, auth_headers):
        response = await client.get("/api/collector/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "earthquake" in data
        assert "weather" in data
        assert "warning" in data

    @pytest.mark.asyncio
    async def test_get_collected_data(self, client, auth_headers):
        response = await client.get("/api/collector/data", headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_latest_events(self, client, auth_headers):
        response = await client.get("/api/collector/events", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.integration
class TestDatasourcesAPI:
    """数据源管理接口"""

    @pytest.mark.asyncio
    async def test_list_datasources(self, client, auth_headers):
        response = await client.get("/api/datasources", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_create_datasource(self, client, auth_headers):
        response = await client.post("/api/datasources", json={
            "name": "测试源", "type": "weather", "url": "http://test.com", "fetch_interval": 3600, "is_active": True
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "测试源"


@pytest.mark.integration
class TestUsersAPI:
    """用户管理接口"""

    @pytest.mark.asyncio
    async def test_list_users(self, client, auth_headers):
        response = await client.get("/api/users", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client, auth_headers):
        response = await client.get("/api/users/99999", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_and_delete_user(self, client, auth_headers):
        create_resp = await client.post("/api/users", json={
            "username": "test_user_temp", "password": "123456", "real_name": "测试", "role_id": 2
        }, headers=auth_headers)
        assert create_resp.status_code == 201
        user_id = create_resp.json()["id"]
        delete_resp = await client.delete(f"/api/users/{user_id}", headers=auth_headers)
        assert delete_resp.status_code == 204


@pytest.mark.integration
class TestAuditAPI:
    """审计日志接口"""

    @pytest.mark.asyncio
    async def test_list_audit_logs(self, client, auth_headers):
        response = await client.get("/api/audit", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_filter_audit_logs(self, client, auth_headers):
        response = await client.get("/api/audit?resource_type=incident&limit=10", headers=auth_headers)
        assert response.status_code == 200
