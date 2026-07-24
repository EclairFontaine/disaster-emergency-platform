from datetime import datetime, timezone
from typing import Optional

from app.services.collectors.earthquake import EarthquakeCollector
from app.services.collectors.weather import WeatherCollector
from app.services.collectors.warning import WarningCollector
from app.services.collectors.gdacs import GdacsCollector

earthquake_collector = EarthquakeCollector()
weather_collector = WeatherCollector()
warning_collector = WarningCollector()
gdacs_collector = GdacsCollector()

CACHE: dict = {
    "earthquake": {"data": [], "time": None},
    "weather": {"data": [], "time": None},
    "warning": {"data": [], "time": None},
    "gdacs": {"data": [], "time": None},
}


async def collect_all() -> dict:
    results = {}
    for name, collector in [
        ("earthquake", earthquake_collector),
        ("weather", weather_collector),
        ("warning", warning_collector),
        ("gdacs", gdacs_collector),
    ]:
        try:
            data = await collector.run()
            CACHE[name] = {"data": data, "time": datetime.now(timezone.utc).isoformat()}
            results[name] = {"status": "ok", "count": len(data)}
        except Exception as e:
            results[name] = {"status": "error", "message": str(e)}
    return results


async def collect_earthquake() -> dict:
    data = await earthquake_collector.run()
    CACHE["earthquake"] = {"data": data, "time": datetime.now(timezone.utc).isoformat()}
    return data


async def collect_weather() -> dict:
    data = await weather_collector.run()
    CACHE["weather"] = {"data": data, "time": datetime.now(timezone.utc).isoformat()}
    return data


async def collect_warnings() -> dict:
    data = await warning_collector.run()
    CACHE["warning"] = {"data": data, "time": datetime.now(timezone.utc).isoformat()}
    return data


async def collect_gdacs() -> dict:
    data = await gdacs_collector.run()
    CACHE["gdacs"] = {"data": data, "time": datetime.now(timezone.utc).isoformat()}
    return data


def get_cached_data(source: Optional[str] = None) -> dict:
    if source:
        return CACHE.get(source, {"data": [], "time": None})
    return CACHE
