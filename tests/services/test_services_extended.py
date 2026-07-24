"""服务层扩展单元测试 — Agent、采集、入库、资源调度"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


@pytest.mark.unit
class TestAgentRunner:
    """Agent执行器"""

    @pytest.mark.asyncio
    async def test_create_agent_run(self):
        from app.services.agent_runner import create_agent_run
        from app.models.all import AgentRun
        db = AsyncMock()

        run = await create_agent_run(db, 1, "generate", {"title": "test"})
        db.add.assert_called_once()
        db.flush.assert_called()
        assert run.incident_id == 1
        assert run.run_type == "generate"
        assert run.status == "running"
        assert run.input_data == {"title": "test"}

    @pytest.mark.asyncio
    async def test_create_agent_run_default_input(self):
        from app.services.agent_runner import create_agent_run
        db = AsyncMock()
        run = await create_agent_run(db, 1, "extract")
        assert run.input_data == {}
        assert run.run_type == "extract"

    @pytest.mark.asyncio
    async def test_finish_agent_run_success(self):
        from app.services.agent_runner import finish_agent_run
        from app.models.all import AgentRun
        db = AsyncMock()
        run = AgentRun(id=1, incident_id=1, run_type="generate", status="running")

        await finish_agent_run(db, run, output_data={"plan_id": 1})
        assert run.status == "completed"
        assert run.output_data == {"plan_id": 1}
        assert run.error_message is None
        assert run.finished_at is not None

    @pytest.mark.asyncio
    async def test_finish_agent_run_error(self):
        from app.services.agent_runner import finish_agent_run
        from app.models.all import AgentRun
        db = AsyncMock()
        run = AgentRun(id=1, incident_id=1, run_type="generate", status="running")

        await finish_agent_run(db, run, error="AI调用超时")
        assert run.status == "failed"
        assert run.error_message == "AI调用超时"
        assert run.output_data is None or run.output_data == {}


@pytest.mark.unit
class TestDeepSeekClient:
    """DeepSeek客户端细节"""

    def test_system_prompts_content(self):
        from app.services.deepseek import SYSTEM_PROMPTS
        for key in ["extract", "generate_plan", "review_plan", "retrieve_keywords"]:
            assert len(SYSTEM_PROMPTS[key]) > 20

    def test_deepseek_client_singleton(self):
        from app.services.deepseek import deepseek_client, DeepSeekClient
        assert isinstance(deepseek_client, DeepSeekClient)

    def test_stream_generator_creation(self):
        from app.services.deepseek import DeepSeekClient
        client = DeepSeekClient()
        assert client._client is None


@pytest.mark.unit
class TestIngestionPipeline:
    """采集入库管线"""

    @pytest.mark.asyncio
    async def test_run_ingestion_calls_both_pipelines(self):
        from app.services.ingestion import run_ingestion
        db = AsyncMock()
        with patch("app.services.ingestion.ingest_earthquake_events", new_callable=AsyncMock) as mock_eq, \
             patch("app.services.ingestion.ingest_weather_events", new_callable=AsyncMock) as mock_wx:
            mock_eq.return_value = [1, 2]
            mock_wx.return_value = [3]
            result = await run_ingestion(db)
            assert result["earthquake"] == [1, 2]
            assert result["weather"] == [3]
            mock_eq.assert_called_once()
            mock_wx.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_ingestion_handles_errors(self):
        from app.services.ingestion import run_ingestion
        db = AsyncMock()
        with patch("app.services.ingestion.ingest_earthquake_events", side_effect=Exception("API timeout")), \
             patch("app.services.ingestion.ingest_weather_events", new_callable=AsyncMock) as mock_wx:
            mock_wx.return_value = []
            result = await run_ingestion(db)
            assert "earthquake_error" in result
            assert result["weather"] == []

    @pytest.mark.asyncio
    async def test_get_latest_events(self):
        from app.services.ingestion import get_latest_events
        from app.models.all import CollectedEvent
        db = AsyncMock()
        result = MagicMock()
        event = CollectedEvent(id=1, source="USGS", event_type="earthquake", title="M5.0")
        result.scalars.return_value.all.return_value = [event]
        db.execute.return_value = result
        events = await get_latest_events(db, limit=5)
        assert len(events) == 1
        assert events[0].source == "USGS"


@pytest.mark.unit
class TestCollectorOrchestration:
    """采集器编排层"""

    def test_get_cached_data_all(self):
        from app.services.collector import get_cached_data
        data = get_cached_data()
        assert isinstance(data, dict)
        assert "earthquake" in data
        assert "weather" in data
        assert "warning" in data

    def test_get_cached_data_source_filter(self):
        from app.services.collector import get_cached_data
        data = get_cached_data("earthquake")
        assert "data" in data
        assert "time" in data

    @pytest.mark.asyncio
    async def test_collect_all_with_mocks(self):
        from app.services.collector import collect_all
        with patch("app.services.collector.earthquake_collector", autospec=True) as mock_eq, \
             patch("app.services.collector.weather_collector", autospec=True) as mock_wx, \
             patch("app.services.collector.warning_collector", autospec=True) as mock_wn:
            mock_eq.run = AsyncMock(return_value=[{"mag": 3.0}])
            mock_wx.run = AsyncMock(return_value=[{"city": "昆明"}])
            mock_wn.run = AsyncMock(return_value=[{"title": "暴雨预警"}])
            results = await collect_all()
            assert results["earthquake"]["status"] == "ok"
            assert results["weather"]["status"] == "ok"
            assert results["warning"]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_collect_all_handles_error(self):
        from app.services.collector import collect_all
        with patch("app.services.collector.earthquake_collector", autospec=True) as mock_eq, \
             patch("app.services.collector.weather_collector", autospec=True) as mock_wx, \
             patch("app.services.collector.warning_collector", autospec=True) as mock_wn:
            mock_eq.run = AsyncMock(side_effect=Exception("network error"))
            mock_wx.run = AsyncMock(return_value=[])
            mock_wn.run = AsyncMock(return_value=[])
            results = await collect_all()
            assert results["earthquake"]["status"] == "error"
            assert "message" in results["earthquake"]


@pytest.mark.unit
class TestResourceAutoDispatcher:
    """自动资源调度"""

    def test_resource_templates_coverage(self):
        from app.services.resource_auto_dispatcher import RESOURCE_TEMPLATES
        required = {"earthquake", "landslide", "flood", "fire", "other"}
        assert set(RESOURCE_TEMPLATES.keys()) == required

    def test_template_types(self):
        from app.services.resource_auto_dispatcher import RESOURCE_TEMPLATES
        expected_types = {"personnel", "vehicle", "material", "shelter"}
        for rules in RESOURCE_TEMPLATES.values():
            actual_types = {r["type"] for r in rules}
            intersection = actual_types.intersection(expected_types)
            assert len(intersection) >= 3

    @pytest.mark.asyncio
    async def test_auto_match_no_resources(self):
        from app.services.resource_auto_dispatcher import auto_match_and_dispatch
        from app.models.all import Incident
        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        db.execute.return_value = result
        incident = Incident(id=1, title="test", category="earthquake", severity="P2", latitude=25.0, longitude=102.0)
        dispatches = await auto_match_and_dispatch(db, incident, 1)
        assert dispatches == []

    @pytest.mark.asyncio
    async def test_auto_match_with_resources(self):
        from app.services.resource_auto_dispatcher import auto_match_and_dispatch
        from app.models.all import Incident, Resource
        db = AsyncMock()
        resources = [
            Resource(id=1, type="personnel", name="消防队", quantity=100, available_qty=90, locked_qty=10, latitude=25.04, longitude=102.68, status="idle"),
            Resource(id=2, type="vehicle", name="救护车", quantity=50, available_qty=50, locked_qty=0, latitude=25.1, longitude=102.7, status="idle"),
            Resource(id=3, type="material", name="帐篷", quantity=1000, available_qty=1000, locked_qty=0, latitude=25.2, longitude=102.8, status="idle"),
            Resource(id=4, type="shelter", name="避难所", quantity=1, available_qty=1, locked_qty=0, latitude=25.3, longitude=102.9, status="idle"),
        ]
        result = MagicMock()
        result.scalars.return_value.all.return_value = resources
        db.execute.return_value = result

        incident = Incident(id=1, title="地震", category="earthquake", severity="P2", latitude=25.0, longitude=102.0)
        dispatches = await auto_match_and_dispatch(db, incident, 1)
        assert len(dispatches) >= 1
        for d in dispatches:
            assert "dispatch_id" in d
            assert "resource_name" in d
            assert "quantity" in d


@pytest.mark.unit
class TestResourceSchedulerExtended:
    """资源调度扩展测试"""

    @pytest.mark.asyncio
    async def test_lock_resource_insufficient(self):
        from app.services.resource_scheduler import lock_resource
        from app.models.all import Resource
        db = AsyncMock()
        result = MagicMock()
        resource = Resource(id=1, type="personnel", name="test", quantity=10, available_qty=10, locked_qty=8)
        result.scalar_one_or_none.return_value = resource
        db.execute.return_value = result

        success = await lock_resource(db, 1, 1, 3, 1)
        assert not success

    @pytest.mark.asyncio
    async def test_lock_resource_success(self):
        from app.services.resource_scheduler import lock_resource
        from app.models.all import Resource
        db = AsyncMock()
        result = MagicMock()
        resource = Resource(id=1, type="personnel", name="test", quantity=10, available_qty=10, locked_qty=2)
        result.scalar_one_or_none.return_value = resource
        db.execute.return_value = result

        success = await lock_resource(db, 1, 1, 5, 1)
        assert success
        assert resource.locked_qty == 7

    @pytest.mark.asyncio
    async def test_lock_resource_not_found(self):
        from app.services.resource_scheduler import lock_resource
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute.return_value = result

        success = await lock_resource(db, 999, 1, 1, 1)
        assert not success

    @pytest.mark.asyncio
    async def test_release_incident_resources(self):
        from app.services.resource_scheduler import release_incident_resources
        from app.models.all import ResourceLock
        db = AsyncMock()
        lock = ResourceLock(id=1, resource_id=1, incident_id=5, quantity=3, locked_by=1)
        result = MagicMock()
        result.scalars.return_value.all.return_value = [lock]
        db.execute.return_value = result

        with patch("app.services.resource_scheduler.release_resource", new_callable=AsyncMock) as mock_release:
            mock_release.return_value = True
            await release_incident_resources(db, 5)
            mock_release.assert_called_once_with(db, lock.id)


@pytest.mark.unit
class TestRAGExtended:
    """RAG检索扩展"""

    @pytest.mark.asyncio
    async def test_match_plans_keyword_filtering(self):
        from app.services.rag import match_plans
        db = AsyncMock()
        db.execute = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        db.execute.return_value = result
        plans = await match_plans(db, ["地震", "应急", "救援"])
        assert plans == []

    @pytest.mark.asyncio
    async def test_search_plans_empty_keywords(self):
        from app.services.rag import search_plans
        db = AsyncMock()
        db.execute = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        db.execute.return_value = result
        plans = await search_plans(db, "地震 洪水")
        assert plans == []


@pytest.mark.unit
class TestAuditExtended:
    """审计日志扩展"""

    @pytest.mark.asyncio
    async def test_get_audit_logs_with_filters(self):
        from app.services.audit import get_audit_logs
        db = AsyncMock()
        db.execute = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        db.execute.return_value = result
        logs = await get_audit_logs(db, user_id=1, resource_type="incident", limit=10, offset=0)
        assert logs == []

    @pytest.mark.asyncio
    async def test_get_audit_logs_no_filters(self):
        from app.services.audit import get_audit_logs
        db = AsyncMock()
        db.execute = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        db.execute.return_value = result
        logs = await get_audit_logs(db)
        assert logs == []


@pytest.mark.unit
class TestCollectorPlugins:
    """采集器插件细节"""

    def test_cities_count(self):
        from app.services.collectors.weather import WeatherCollector
        c = WeatherCollector()
        assert any(city["name"] == "普洱" for city in c.CITIES)
        assert all("qweather_id" in city for city in c.CITIES)

    @pytest.mark.asyncio
    async def test_weather_collect_no_api_key(self):
        from app.services.collectors.weather import WeatherCollector
        c = WeatherCollector()
        with patch.object(c, "collect_from_qweather", new_callable=AsyncMock) as mock_qw, \
             patch.object(c, "collect_from_openweather", new_callable=AsyncMock) as mock_ow:
            mock_qw.return_value = [{"source": "QWeather", "error": "no key"}]
            mock_ow.return_value = []
            result = await c.collect()
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_warning_collector_collect(self):
        from app.services.collectors.warning import WarningCollector
        c = WarningCollector()
        with patch.object(c, "collect_from_gdweather", new_callable=AsyncMock) as mock_gd:
            mock_gd.return_value = []
            result = await c.collect()
            assert result == []

    def test_earthquake_collector_query_params(self):
        from app.services.collectors.earthquake import EarthquakeCollector
        collector = EarthquakeCollector()
        assert collector.url
        assert "usgs.gov" in collector.url

    def test_base_collector_abstract(self):
        from app.services.collectors.base import BaseCollector
        collector = BaseCollector(name="test", url="http://test", interval=60)
        with pytest.raises(NotImplementedError):
            import asyncio
            asyncio.run(collector.collect())


@pytest.mark.unit
class TestAITemplateEngine:
    """AI模板引擎降级"""

    @pytest.mark.asyncio
    async def test_template_generates_all_sections(self):
        from app.services.ai_engine import generate_plan_with_template
        from app.models.all import Incident, AgentRun
        db = AsyncMock()
        with patch("app.services.ai_engine.search_plans", new_callable=AsyncMock) as mock_search, \
             patch("app.services.ai_engine.search_historical_events", new_callable=AsyncMock) as mock_hist:
            mock_search.return_value = []
            mock_hist.return_value = []
            incident = Incident(id=1, title="测试地震", category="earthquake", severity="P2",
                                description="强烈地震", latitude=25.0, longitude=102.0, affected_count=1000)
            run = AgentRun(id=1, incident_id=1, run_type="generate", status="running", input_data={})
            content, refs = await generate_plan_with_template(db, incident, run)
            assert "应急处置方案" in content
            assert "灾情概述" in content
            assert "应急响应等级" in content
            assert "组织机构与职责" in content
            assert "处置措施" in content
            assert incident.title in content
            assert isinstance(refs, list)

    @pytest.mark.asyncio
    async def test_template_includes_plans_if_available(self):
        from app.services.ai_engine import generate_plan_with_template
        from app.models.all import Incident, AgentRun, EmergencyPlan
        db = AsyncMock()
        plan = EmergencyPlan(id=1, title="云南地震预案", content="地震应急措施说明" * 5)
        with patch("app.services.ai_engine.search_plans", new_callable=AsyncMock) as mock_search, \
             patch("app.services.ai_engine.search_historical_events", new_callable=AsyncMock) as mock_hist:
            mock_search.return_value = [plan]
            mock_hist.return_value = []
            incident = Incident(id=1, title="测试", category="earthquake", severity="P2",
                                description="地震", latitude=25.0, longitude=102.0)
            run = AgentRun(id=1, incident_id=1, run_type="generate", status="running", input_data={})
            content, refs = await generate_plan_with_template(db, incident, run)
            assert "参考预案" in content
            assert len(refs) >= 1
            assert refs[0]["doc_name"] == "云南地震预案"


@pytest.mark.unit
class TestConfigExtended:
    """配置扩展测试"""

    def test_settings_has_all_required(self):
        from app.core.config import settings
        required = ["APP_NAME", "DATABASE_URL", "JWT_SECRET", "DEEPSEEK_API_KEY", "CORS_ORIGINS"]
        for key in required:
            assert hasattr(settings, key)

    def test_env_file_parsing_order(self):
        from app.core.config import Settings
        s = Settings()
        assert s.APP_NAME
        assert s.JWT_ALGORITHM == "HS256"
        assert s.JWT_EXPIRE_MINUTES > 0
