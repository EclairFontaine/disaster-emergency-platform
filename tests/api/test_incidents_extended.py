"""灾情管理 API 扩展集成测试"""
import pytest


@pytest.mark.integration
class TestIncidentsExtended:

    @pytest.fixture
    async def first_incident_id(self, client, auth_headers):
        resp = await client.get("/api/incidents", headers=auth_headers)
        incidents = resp.json()
        return incidents[0]["id"] if incidents else 1

    @pytest.mark.asyncio
    async def test_create_incident(self, client, auth_headers):
        response = await client.post("/api/incidents", json={
            "title": "测试灾情",
            "description": "集成测试灾情描述",
            "category": "earthquake",
            "severity": "P3",
            "latitude": 25.0,
            "longitude": 102.0,
            "affected_count": 100,
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "测试灾情"
        assert data["category"] == "earthquake"

    @pytest.mark.asyncio
    async def test_update_incident(self, client, auth_headers):
        create_resp = await client.post("/api/incidents", json={
            "title": "待更新灾情", "severity": "P4",
        }, headers=auth_headers)
        incident_id = create_resp.json()["id"]
        response = await client.put(f"/api/incidents/{incident_id}", json={
            "title": "已更新灾情", "severity": "P2", "description": "更新后的描述"
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "已更新灾情"
        assert data["severity"] == "P2"

    @pytest.mark.asyncio
    async def test_status_transition(self, client, auth_headers):
        create_resp = await client.post("/api/incidents", json={
            "title": "状态流转测试", "severity": "P3",
        }, headers=auth_headers)
        incident_id = create_resp.json()["id"]
        response = await client.put(f"/api/incidents/{incident_id}/status", json={
            "status": "confirmed", "reason": "确认为真实灾情"
        }, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"

    @pytest.mark.asyncio
    async def test_invalid_status_transition(self, client, auth_headers):
        create_resp = await client.post("/api/incidents", json={
            "title": "非法流转测试", "severity": "P4",
        }, headers=auth_headers)
        incident_id = create_resp.json()["id"]
        response = await client.put(f"/api/incidents/{incident_id}/status", json={
            "status": "closed", "reason": "跳过确认直接关闭"
        }, headers=auth_headers)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_report(self, client, auth_headers, first_incident_id):
        response = await client.post(f"/api/incidents/{first_incident_id}/reports", json={
            "content": "灾情补充说明",
            "contact_info": "13800138000",
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "灾情补充说明"
        assert data["incident_id"] == first_incident_id

    @pytest.mark.asyncio
    async def test_list_reports(self, client, auth_headers, first_incident_id):
        await client.post(f"/api/incidents/{first_incident_id}/reports", json={
            "content": "临时报告",
        }, headers=auth_headers)
        response = await client.get(f"/api/incidents/{first_incident_id}/reports", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_nearby_incidents(self, client, auth_headers):
        response = await client.get(
            "/api/incidents/nearby",
            params={"lat": 25.04, "lng": 102.68, "radius": 50000},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_filter_by_status(self, client, auth_headers):
        response = await client.get("/api/incidents?status=pending_review", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(i["status"] == "pending_review" for i in data)

    @pytest.mark.asyncio
    async def test_filter_by_category(self, client, auth_headers):
        response = await client.get("/api/incidents?category=earthquake", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(i["category"] == "earthquake" for i in data)
