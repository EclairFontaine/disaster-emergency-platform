import httpx
import asyncio
from datetime import datetime, timezone
from typing import Optional

class BaseCollector:
    def __init__(self, name: str, url: str, interval: int = 3600):
        self.name = name
        self.url = url
        self.interval = interval
        self.last_fetch: Optional[datetime] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def fetch(self, url: str, params: dict = None) -> dict:
        client = await self._get_client()
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    async def collect(self) -> list[dict]:
        raise NotImplementedError

    async def run(self) -> list[dict]:
        data = await self.collect()
        self.last_fetch = datetime.now(timezone.utc)
        return data
