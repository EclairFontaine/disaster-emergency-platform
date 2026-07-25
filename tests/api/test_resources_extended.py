"""资源管理 API 扩展集成测试"""
import pytest


@pytest.mark.integration
class TestResourcesExtended:

    @pytest.fixture
    async def real_ids(self, client, auth_headers):
        inc_resp = await client.get("/api/incidents", headers=auth_headers)
        incidents = inc_resp.json()
        res_resp = await client.get("/api/resources", headers=auth_headers)
        resources = res_resp.json()
        return {
            "incident_id": incidents[0]["id"] if incidents else 1,
            "resource_id": resources[0]["id"] if resources else 1,
        }

    @pytest.mark.asyncio
    async def test_create_resource(self, client, auth_headers):
        response = await client.post("/api/resources", json={
            "type": "personnel",
            "name": "测试救援队",
            "description": "集成测试用资源",
            "quantity": 50,
            "available_qty": 50,
            "latitude": 25.04,
            "longitude": 102.68,
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "测试救援队"
        assert data["type"] == "personnel"

    @pytest.mark.asyncio
    async def test_get_resource(self, client, auth_headers):
        create_resp = await client.post("/api/resources", json={
            "type": "material", "name": "临时物资", "quantity": 100,
        }, headers=auth_headers)
        resource_id = create_resp.json()["id"]
        response = await client.get(f"/api/resources/{resource_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == resource_id

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, client, auth_headers):
        response = await client.get("/api/resources/99999", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_resource(self, client, auth_headers):
        create_resp = await client.post("/api/resources", json={
            "type": "vehicle", "name": "旧名称", "quantity": 10,
        }, headers=auth_headers)
        resource_id = create_resp.json()["id"]
        response = await client.put(f"/api/resources/{resource_id}", json={
            "name": "新名称", "quantity": 20
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "新名称"
        assert data["quantity"] == 20

    @pytest.mark.asyncio
    async def test_delete_resource(self, client, auth_headers):
        create_resp = await client.post("/api/resources", json={
            "type": "material", "name": "待删除资源", "quantity": 1,
        }, headers=auth_headers)
        resource_id = create_resp.json()["id"]
        response = await client.delete(f"/api/resources/{resource_id}", headers=auth_headers)
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_lock_resource(self, client, auth_headers, real_ids):
        create_resp = await client.post("/api/resources", json={
            "type": "personnel", "name": "可锁定资源", "quantity": 100, "available_qty": 100,
        }, headers=auth_headers)
        resource_id = create_resp.json()["id"]
        response = await client.post(
            f"/api/resources/{resource_id}/lock",
            json={"incident_id": real_ids["incident_id"], "quantity": 10}, headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_lock_insufficient_resource(self, client, auth_headers, real_ids):
        create_resp = await client.post("/api/resources", json={
            "type": "shelter", "name": "小容量资源", "quantity": 5, "available_qty": 5,
        }, headers=auth_headers)
        resource_id = create_resp.json()["id"]
        response = await client.post(
            f"/api/resources/{resource_id}/lock",
            json={"incident_id": real_ids["incident_id"], "quantity": 999}, headers=auth_headers
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_filter_by_type(self, client, auth_headers):
        response = await client.get("/api/resources?type=personnel", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(r["type"] == "personnel" for r in data)
