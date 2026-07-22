import httpx
from typing import AsyncGenerator, Optional
from app.core.config import settings


SYSTEM_PROMPTS = {
    "extract": "你是一个灾害信息抽取助手。根据灾情描述，提取结构化的灾害信息，以JSON格式返回。包含：灾害类型、严重程度、影响范围、建议响应级别。",
    "retrieve_keywords": "你是一个应急关键词提取助手。根据灾情描述，提取3-5个核心关键词用于检索应急预案，以逗号分隔。",
    "generate_plan": "你是一个应急管理专家。根据灾情信息和参考预案，生成一份详细的应急处置方案。方案需包含：一、灾情概述；二、应急响应等级；三、组织机构与职责；四、处置措施；五、资源调配方案；六、注意事项。请使用专业、规范的表述。",
    "review_plan": "你是一个应急方案审查专家。审查给定的应急处置方案，指出存在的问题和改进建议。",
}


class DeepSeekClient:
    def __init__(self):
        self.base_url = settings.DEEPSEEK_BASE_URL.rstrip("/")
        self.api_key = settings.DEEPSEEK_API_KEY
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(120.0))
        return self._client

    async def chat_completion(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ):
        client = await self._get_client()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        if stream:

            async def stream_generator() -> AsyncGenerator[str, None]:
                async with client.stream("POST", f"{self.base_url}/chat/completions", headers=headers, json=body) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            yield data

            return stream_generator()
        else:
            response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=body)
            response.raise_for_status()
            return response.json()

    async def get_embedding(self, text: str) -> list[float]:
        client = await self._get_client()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": "text-embedding-ada-002",
            "input": text,
        }
        response = await client.post(f"{self.base_url}/embeddings", headers=headers, json=body)
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None


deepseek_client = DeepSeekClient()
