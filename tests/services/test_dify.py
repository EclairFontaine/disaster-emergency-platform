"""Dify 服务单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.unit
class TestDifyClient:

    def test_init(self):
        from app.services.dify import DifyClient, dify_client
        assert isinstance(dify_client, DifyClient)

    def test_base_url_configured(self):
        from app.services.dify import DifyClient
        client = DifyClient()
        assert client.api_key is not None
        assert client.base_url is not None

    @pytest.mark.asyncio
    async def test_chat_blocking(self):
        from app.services.dify import DifyClient
        client = DifyClient()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "answer": "应急方案已生成",
            "conversation_id": "conv-001",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await client.chat_blocking(
                query="生成地震应急方案",
                inputs={"category": "earthquake"},
            )
            assert result["answer"] == "应急方案已生成"
            assert result["conversation_id"] == "conv-001"

    @pytest.mark.asyncio
    async def test_chat_blocking_with_empty_inputs(self):
        from app.services.dify import DifyClient
        client = DifyClient()
        mock_response = MagicMock()
        mock_response.json.return_value = {"answer": "ok"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await client.chat_blocking(query="test")
            assert result["answer"] == "ok"

    @pytest.mark.asyncio
    async def test_chat_streaming(self):
        from app.services.dify import DifyClient
        client = DifyClient()
        lines = [
            'data: {"event":"message","answer":"第一步"}\n\n',
            'data: {"event":"message","answer":"第二步"}\n\n',
        ]

        class MockStreamCtx:
            async def raise_for_status(self): pass
            async def aiter_lines(self):
                for line in lines:
                    yield line
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args): pass

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http = MagicMock()
            mock_http.stream = MagicMock()
            mock_http.stream.return_value = MockStreamCtx()
            mock_get_client.return_value = mock_http

            chunks = []
            async for chunk in client.chat_streaming(query="test"):
                chunks.append(chunk)
            assert len(chunks) == 2

    @pytest.mark.asyncio
    async def test_close(self):
        from app.services.dify import DifyClient
        client = DifyClient()
        client._client = AsyncMock()
        await client.close()
        assert client._client is None
