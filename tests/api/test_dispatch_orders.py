"""调度单 API 集成测试"""
import pytest


@pytest.mark.integration
class TestDispatchOrdersAPI:

    @pytest.fixture
    async def real_ids(self, client, auth_headers):
        inc_resp = await client.get("/api/incidents", headers=auth_headers)
        incidents = inc_resp.json()
        res_resp = await client.get("/api/resources", headers=auth_headers)
        resources = res_resp.json()
        return {
            "incident_id": incidents[0]["id"] if incidents else 1,
            "resource_id": resources[0]["id"] if resources else 1,
            "incident_id_2": incidents[1]["id"] if len(incidents) > 1 else incidents[0]["id"],
        }

    @pytest.mark.asyncio
    async def test_list_empty(self, client, auth_headers):
        response = await client.get("/api/dispatch-orders", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_create_dispatch_order(self, client, auth_headers, real_ids):
        response = await client.post("/api/dispatch-orders", json={
            "incident_id": real_ids["incident_id"],
            "resource_id": real_ids["resource_id"],
            "quantity": 10,
            "dest_latitude": 25.04,
            "dest_longitude": 102.68,
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["incident_id"] == real_ids["incident_id"]
        assert data["quantity"] == 10
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_dispatch_order(self, client, auth_headers, real_ids):
        create_resp = await client.post("/api/dispatch-orders", json={
            "incident_id": real_ids["incident_id"],
            "resource_id": real_ids["resource_id"],
            "quantity": 5,
        }, headers=auth_headers)
        order_id = create_resp.json()["id"]
        response = await client.get(f"/api/dispatch-orders/{order_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == order_id

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, client, auth_headers):
        response = await client.get("/api/dispatch-orders/99999", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_status_approved(self, client, auth_headers, real_ids):
        create_resp = await client.post("/api/dispatch-orders", json={
            "incident_id": real_ids["incident_id"],
            "resource_id": real_ids["resource_id"],
            "quantity": 3,
        }, headers=auth_headers)
        order_id = create_resp.json()["id"]
        response = await client.put(
            f"/api/dispatch-orders/{order_id}/status",
            json={"status": "approved"}, headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "approved"

    @pytest.mark.asyncio
    async def test_status_flow(self, client, auth_headers, real_ids):
        create_resp = await client.post("/api/dispatch-orders", json={
            "incident_id": real_ids["incident_id"],
            "resource_id": real_ids["resource_id"],
            "quantity": 2,
        }, headers=auth_headers)
        order_id = create_resp.json()["id"]

        for status in ["approved", "in_transit", "arrived"]:
            resp = await client.put(
                f"/api/dispatch-orders/{order_id}/status",
                json={"status": status}, headers=auth_headers
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == status

    @pytest.mark.asyncio
    async def test_filter_by_incident(self, client, auth_headers, real_ids):
        create_resp = await client.post("/api/dispatch-orders", json={
            "incident_id": real_ids["incident_id"],
            "resource_id": real_ids["resource_id"],
            "quantity": 1,
        }, headers=auth_headers)
        assert create_resp.status_code == 201
        response = await client.get(
            f"/api/dispatch-orders?incident_id={real_ids['incident_id']}",
            headers=auth_headers
        )
        assert response.status_code == 200
        orders = response.json()
        assert all(o["incident_id"] == real_ids["incident_id"] for o in orders)

    @pytest.mark.asyncio
    async def test_unauthorized_create(self, client):
        response = await client.post("/api/dispatch-orders", json={
            "incident_id": 1, "resource_id": 1, "quantity": 1,
        })
        assert response.status_code in (401, 403)
