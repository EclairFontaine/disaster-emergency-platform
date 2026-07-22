from datetime import datetime, timezone
from .base import BaseCollector


class WarningCollector(BaseCollector):
    """预警信息采集"""

    def __init__(self):
        super().__init__(name="预警信息", url="", interval=3600)

    async def collect_from_gdweather(self) -> list[dict]:
        """国家突发事件预警信息发布网"""
        now = datetime.now(timezone.utc)
        try:
            data = await self.fetch("http://www.12379.cn/data/alarm_list.json")
            warnings = []
            for item in data[:50]:
                warnings.append({
                    "source": "国家预警中心",
                    "alert_id": item.get("alertid"),
                    "title": item.get("headline", ""),
                    "type": item.get("alarmtype", ""),
                    "level": item.get("alarmlevel", ""),
                    "content": item.get("description", ""),
                    "region": item.get("provincename", "") + item.get("cityname", ""),
                    "issue_time": item.get("issuetime"),
                    "fetch_time": now.isoformat(),
                })
            return warnings
        except Exception as e:
            return [{"source": "国家预警中心", "error": str(e), "fetch_time": now.isoformat()}]

    async def collect(self) -> list[dict]:
        return await self.collect_from_gdweather()
