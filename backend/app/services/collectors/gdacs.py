"""GDACS 全球灾害预警采集器 — 覆盖西南+东南亚"""
from datetime import datetime, timezone, timedelta
from .base import BaseCollector

GDACS_URL = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH"

class GdacsCollector(BaseCollector):
    """GDACS 免费全球灾害数据：热带气旋/洪水/火山/地震"""

    def __init__(self):
        super().__init__(name="GDACS", url=GDACS_URL, interval=3600)

    # 宽区域：覆盖中国西南+东南亚+南亚
    REGION = (10.0, 40.0, 85.0, 130.0)
    
    TYPE_MAP = {"EQ": "earthquake", "TC": "other", "FL": "flood", "VO": "other", "DR": "other"}
    TYPE_LABELS = {"EQ": "地震", "TC": "热带气旋", "FL": "洪水", "VO": "火山", "DR": "干旱"}
    SEVERITY_MAP = {"Green": 1, "Orange": 2, "Red": 3}

    async def collect(self) -> list[dict]:
        now = datetime.now(timezone.utc)
        start = (now - timedelta(days=7)).strftime("%Y-%m-%d")

        try:
            data = await self.fetch(GDACS_URL, params={
                "fromDate": start,
                "toDate": now.strftime("%Y-%m-%d"),
            })
            events = []
            lat_min, lat_max, lng_min, lng_max = self.REGION

            for feature in data.get("features", [])[:50]:
                props = feature.get("properties", {})
                geom = feature.get("geometry", {})
                coords = geom.get("coordinates", [0, 0])
                lng, lat = float(coords[0]), float(coords[1])

                # 区域过滤
                if not (lat_min <= lat <= lat_max and lng_min <= lng <= lng_max):
                    continue

                etype = props.get("eventtype", "EQ")
                alert = props.get("alertlevel", "Green")
                sev_num = self.SEVERITY_MAP.get(alert, 1)
                label = self.TYPE_LABELS.get(etype, "灾害")
                event_name = props.get("eventname", "Unknown")

                events.append({
                    "source": "GDACS",
                    "event_id": str(props.get("eventid", "")),
                    "title": f"{label}预警：{event_name}",
                    "event_type": self.TYPE_MAP.get(etype, "other"),
                    "gdacs_type": etype,
                    "magnitude": sev_num,
                    "alert_level": alert,
                    "latitude": lat,
                    "longitude": lng,
                    "place": props.get("description", ""),
                    "fetch_time": now.isoformat(),
                })
            return events if events else []
        except Exception as e:
            return [{"source": "GDACS", "error": str(e), "fetch_time": now.isoformat()}]
