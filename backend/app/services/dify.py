import httpx
import json as json_mod
from typing import AsyncGenerator, Optional
from app.core.config import settings


class DifyClient:
    def __init__(self):
        self.base_url = settings.DIFY_API_URL.rstrip("/")
        self.api_key = settings.DIFY_API_KEY
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(120.0))
        return self._client

    async def chat_blocking(
        self,
        query: str,
        inputs: dict = None,
        conversation_id: str = "",
        user: str = "system",
    ) -> dict:
        client = await self._get_client()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": "blocking",
            "conversation_id": conversation_id,
            "user": user,
        }
        response = await client.post(
            f"{self.base_url}/chat-messages", headers=headers, json=body
        )
        response.raise_for_status()
        return response.json()

    async def chat_streaming(
        self,
        query: str,
        inputs: dict = None,
        conversation_id: str = "",
        user: str = "system",
    ) -> AsyncGenerator[str, None]:
        client = await self._get_client()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": "streaming",
            "conversation_id": conversation_id,
            "user": user,
        }
        async with client.stream(
            "POST", f"{self.base_url}/chat-messages", headers=headers, json=body
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    yield data

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None


dify_client = DifyClient()
