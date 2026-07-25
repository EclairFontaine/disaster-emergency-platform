"""性能基准测试 — HTTP API 响应时间采样"""
import asyncio
import time
import statistics
import json
import httpx

BASE_URL = "http://127.0.0.1:8000"
SAMPLES = 20
ENDPOINTS = [
    ("GET", "/api/health"),
    ("GET", "/api/incidents"),
    ("GET", "/api/resources"),
    ("GET", "/api/plans"),
    ("GET", "/api/statistics"),
    ("GET", "/api/users"),
    ("GET", "/api/dispatch-orders"),
    ("GET", "/api/audit"),
    ("GET", "/api/collector/status"),
]


async def measure_endpoint(client, method, url, headers, samples=20):
    times = []
    for _ in range(samples):
        start = time.perf_counter()
        if method == "GET":
            await client.get(url, headers=headers)
        times.append((time.perf_counter() - start) * 1000)
    times.sort()
    return {
        "avg": round(statistics.mean(times), 1),
        "p50": round(times[len(times) // 2], 1),
        "p95": round(times[int(len(times) * 0.95)], 1),
        "p99": round(times[int(len(times) * 0.99)], 1),
        "min": round(times[0], 1),
        "max": round(times[-1], 1),
    }


async def main():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
        r = await client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        results = {}
        total_start = time.perf_counter()
        for method, url in ENDPOINTS:
            need_auth = url != "/api/health"
            h = headers if need_auth else {}
            result = await measure_endpoint(client, method, url, h, SAMPLES)
            results[url] = result
            print(f"  {method} {url:<30s} avg={result['avg']:>6.1f}ms  p50={result['p50']:>6.1f}ms  p95={result['p95']:>6.1f}ms  p99={result['p99']:>6.1f}ms")

        total_time = (time.perf_counter() - total_start) * 1000
        print(f"\n  总计: {total_time:.0f}ms ({SAMPLES}x{len(ENDPOINTS)}={SAMPLES*len(ENDPOINTS)} 请求)")

        report_path = "tests/performance/perf_results.json"
        with open(report_path, "w") as f:
            json.dump({
                "samples_per_endpoint": SAMPLES,
                "total_endpoints": len(ENDPOINTS),
                "total_requests": SAMPLES * len(ENDPOINTS),
                "results": results,
            }, f, indent=2)
        print(f"\n  结果已保存到 {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
