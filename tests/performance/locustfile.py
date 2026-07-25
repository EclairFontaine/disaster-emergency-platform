from locust import HttpUser, task, between

class DisasterPlatformUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        resp = self.client.post("/api/auth/login", json={
            "username": "admin", "password": "admin123"
        })
        self.token = resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(5)
    def list_incidents(self):
        self.client.get("/api/incidents", headers=self.headers)

    @task(4)
    def get_statistics(self):
        self.client.get("/api/statistics", headers=self.headers)

    @task(3)
    def list_resources(self):
        self.client.get("/api/resources", headers=self.headers)

    @task(2)
    def list_plans(self):
        self.client.get("/api/plans", headers=self.headers)

    @task(2)
    def list_dispatch_orders(self):
        self.client.get("/api/dispatch-orders", headers=self.headers)

    @task(1)
    def health_check(self):
        self.client.get("/api/health")
