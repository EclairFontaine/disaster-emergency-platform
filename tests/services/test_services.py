"""服务层单元测试 — 无外部依赖"""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.unit
class TestDeepSeek:
    """DeepSeek客户端配置"""

    def test_system_prompts_loaded(self):
        from app.services.deepseek import SYSTEM_PROMPTS
        assert "extract" in SYSTEM_PROMPTS
        assert "generate_plan" in SYSTEM_PROMPTS
        assert "review_plan" in SYSTEM_PROMPTS
        assert "retrieve_keywords" in SYSTEM_PROMPTS

    def test_deepseek_client_init(self):
        from app.services.deepseek import DeepSeekClient
        client = DeepSeekClient()
        assert client.api_key is not None
        assert client.base_url is not None
        assert "deepseek.com" in client.base_url


@pytest.mark.unit
class TestCollectors:
    """数据采集器初始化"""

    def test_earthquake_collector_init(self):
        from app.services.collectors.earthquake import EarthquakeCollector
        collector = EarthquakeCollector()
        assert collector.name == "地震数据采集"
        assert collector.url

    def test_earthquake_bbox(self):
        from app.services.collectors.earthquake import YUNNAN_BBOX
        assert "minlatitude" in YUNNAN_BBOX
        assert 18.0 <= YUNNAN_BBOX["minlatitude"] <= 32.0

    def test_weather_collector_init(self):
        from app.services.collectors.weather import WeatherCollector
        collector = WeatherCollector()
        assert len(collector.CITIES) == 5
        city_names = [c["name"] for c in collector.CITIES]
        assert "昆明" in city_names

    def test_warning_collector_init(self):
        from app.services.collectors.warning import WarningCollector
        collector = WarningCollector()
        assert collector.name == "预警信息"


@pytest.mark.unit
class TestResourceTemplates:
    """资源自动匹配模板"""

    def test_resource_templates_exist(self):
        from app.services.resource_auto_dispatcher import RESOURCE_TEMPLATES
        required = ["earthquake", "landslide", "flood", "fire", "other"]
        for key in required:
            assert key in RESOURCE_TEMPLATES
            assert len(RESOURCE_TEMPLATES[key]) > 0

    def test_template_has_required_types(self):
        from app.services.resource_auto_dispatcher import RESOURCE_TEMPLATES
        for rules in RESOURCE_TEMPLATES.values():
            types = {r["type"] for r in rules}
            assert len(types) >= 3


@pytest.mark.unit
class TestAudit:
    """审计日志服务"""

    @pytest.mark.asyncio
    async def test_log_action_adds_record(self):
        from app.services.audit import log_action
        db = AsyncMock()
        await log_action(db, 1, "test", "incident", 1, {"key": "value"})
        db.add.assert_called_once()
        assert db.flush.called


@pytest.mark.unit
class TestResourceScheduler:
    """资源调度逻辑"""

    @pytest.mark.asyncio
    async def test_check_conflict_when_insufficient(self):
        from app.services.resource_scheduler import check_conflict
        from app.models.all import Resource
        db = AsyncMock()
        result = MagicMock()
        resource = Resource(id=1, type="personnel", name="test", quantity=10, available_qty=10, locked_qty=3)
        result.scalar_one_or_none.return_value = resource
        db.execute.return_value = result

        has_conflict = await check_conflict(db, 1, 8)
        assert has_conflict

    @pytest.mark.asyncio
    async def test_check_conflict_when_available(self):
        from app.services.resource_scheduler import check_conflict
        from app.models.all import Resource
        db = AsyncMock()
        result = MagicMock()
        resource = Resource(id=1, type="personnel", name="test", quantity=10, available_qty=10, locked_qty=3)
        result.scalar_one_or_none.return_value = resource
        db.execute.return_value = result

        has_conflict = await check_conflict(db, 1, 7)
        assert not has_conflict


@pytest.mark.unit
class TestRAG:
    """RAG检索"""

    @pytest.mark.asyncio
    async def test_search_plans_returns_list(self):
        from app.services.rag import search_plans
        db = AsyncMock()
        db.execute = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        db.execute.return_value = result
        plans = await search_plans(db, "昆明 地震 应急")
        assert plans == []


@pytest.mark.unit
class TestConfig:
    """配置加载"""

    def test_settings_defaults(self):
        from app.core.config import settings
        assert settings.APP_NAME
        assert settings.JWT_SECRET
        assert settings.CORS_ORIGINS

    def test_cors_origins_parsed(self):
        from app.core.config import settings
        origins = settings.cors_origins_list
        assert isinstance(origins, list)
        assert len(origins) > 0
