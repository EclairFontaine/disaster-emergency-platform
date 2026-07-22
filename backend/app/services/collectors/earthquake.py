from datetime import datetime, timezone, timedelta
from .base import BaseCollector

USGS_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
YUNNAN_BBOX = {
    "minlatitude": 21.0,
    "maxlatitude": 29.5,
    "minlongitude": 97.0,
    "maxlongitude": 107.0,
}


class EarthquakeCollector(BaseCollector):
    """采集地震数据 - USGS全球地震API（免费，无需Key）
    中国地震台网(CENC)备用: http://www.ceic.ac.cn
    """

    def __init__(self):
        super().__init__(name="地震数据采集", url=USGS_URL, interval=1800)

    async def collect(self) -> list[dict]:
        now = datetime.now(timezone.utc)
        start = (now - timedelta(days=7)).strftime("%Y-%m-%d")

        params = {
            "format": "geojson",
            "starttime": start,
            "minmagnitude": 2.5,
            "orderby": "time",
            **YUNNAN_BBOX,
        }

        try:
            data = await self.fetch(USGS_URL, params)
            events = []
            for feature in data.get("features", []):
                props = feature["properties"]
                geom = feature["geometry"]
                events.append({
                    "source": "USGS",
                    "event_id": feature["id"],
                    "title": props.get("title", ""),
                    "magnitude": props.get("mag"),
                    "place": props.get("place", ""),
                    "time": props.get("time"),
                    "latitude": geom["coordinates"][1],
                    "longitude": geom["coordinates"][0],
                    "depth": geom["coordinates"][2],
                    "alert": props.get("alert"),
                    "type": props.get("type"),
                    "url": props.get("url"),
                    "fetch_time": now.isoformat(),
                })
            return events
        except Exception as e:
            return [{"source": "USGS", "error": str(e), "fetch_time": now.isoformat()}]


class CeicCollector(BaseCollector):
    """中国地震台网(CENC)数据采集"""

    def __init__(self):
        super().__init__(name="中国地震台网", url="http://www.ceic.ac.cn/ajax/speedsearch", interval=3600)

    async def collect(self) -> list[dict]:
        """中国地震台网最新地震列表"""
        try:
            data = await self.fetch(
                "http://www.ceic.ac.cn/ajax/google",
                params={"rand": "true"},
            )
            events = []
            now = datetime.now(timezone.utc)
            for item in data[:20]:
                magnitude = float(item.get("M", 0))
                lat = float(item.get("EPI_LAT", 0))
                lng = float(item.get("EPI_LON", 0))
                # 检查是否在云南范围
                if 20.8 <= lat <= 29.5 and 97.3 <= lng <= 106.2:
                    events.append({
                        "source": "CENC",
                        "event_id": item.get("EVENT_ID", f"ceic_{item.get('O_TIME')}"),
                        "title": f"{item.get('LOC_NAME_C', '')} M{magnitude}级地震",
                        "magnitude": magnitude,
                        "place": item.get("LOC_NAME_C", ""),
                        "time": item.get("O_TIME", ""),
                        "latitude": lat,
                        "longitude": lng,
                        "depth": float(item.get("EPI_DEPTH", 0)),
                        "type": "earthquake",
                        "fetch_time": now.isoformat(),
                    })
            return events
        except Exception as e:
            return [{"source": "CENC", "error": str(e), "fetch_time": datetime.now(timezone.utc).isoformat()}]
