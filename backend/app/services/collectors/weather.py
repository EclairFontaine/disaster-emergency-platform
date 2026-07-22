from datetime import datetime, timezone
from .base import BaseCollector


class WeatherCollector(BaseCollector):
    """气象数据采集 - OpenWeatherMap + 和风天气"""

    def __init__(self):
        super().__init__(name="气象数据", url="", interval=1800)

    CITIES = [
        {"name": "昆明", "lat": 25.04, "lon": 102.68, "qweather_id": "101290101"},
        {"name": "大理", "lat": 25.59, "lon": 100.23, "qweather_id": "101290201"},
        {"name": "丽江", "lat": 26.87, "lon": 100.23, "qweather_id": "101291401"},
        {"name": "昭通", "lat": 27.34, "lon": 103.72, "qweather_id": "101291001"},
        {"name": "普洱", "lat": 22.78, "lon": 100.97, "qweather_id": "101290901"},
    ]

    async def collect_from_qweather(self) -> list[dict]:
        """和风天气API (https://dev.qweather.com) 免费版每天1000次"""
        from app.core.config import settings
        api_key = settings.QWEATHER_API_KEY
        if not api_key:
            return [{"source": "QWeather", "error": "未配置 QWEATHER_API_KEY", "fetch_time": datetime.now(timezone.utc).isoformat()}]

        now = datetime.now(timezone.utc)
        results = []
        for city in self.CITIES:
            try:
                data = await self.fetch(
                    "https://devapi.qweather.com/v7/weather/now",
                    params={"location": city["qweather_id"], "key": api_key}
                )
                results.append({
                    "source": "QWeather",
                    "city": city["name"],
                    "temperature": data.get("now", {}).get("temp"),
                    "condition": data.get("now", {}).get("text"),
                    "humidity": data.get("now", {}).get("humidity"),
                    "wind": data.get("now", {}).get("windDir"),
                    "fetch_time": now.isoformat(),
                })
            except Exception:
                pass
        return results if results else [{"source": "QWeather", "error": "API调用失败", "fetch_time": now.isoformat()}]

    async def collect_from_openweather(self) -> list[dict]:
        """OpenWeatherMap API"""
        from app.core.config import settings
        api_key = settings.OPENWEATHER_API_KEY
        if not api_key:
            return [{"source": "OpenWeatherMap", "error": "未配置 OPENWEATHER_API_KEY", "fetch_time": datetime.now(timezone.utc).isoformat()}]

        now = datetime.now(timezone.utc)
        results = []
        for city in self.CITIES:
            try:
                data = await self.fetch(
                    "https://api.openweathermap.org/data/2.5/weather",
                    params={
                        "lat": city["lat"], "lon": city["lon"],
                        "appid": api_key, "units": "metric", "lang": "zh_cn",
                    }
                )
                results.append({
                    "source": "OpenWeatherMap",
                    "city": city["name"],
                    "temperature": data.get("main", {}).get("temp"),
                    "humidity": data.get("main", {}).get("humidity"),
                    "condition": data.get("weather", [{}])[0].get("description"),
                    "wind_speed": data.get("wind", {}).get("speed"),
                    "fetch_time": now.isoformat(),
                })
            except Exception:
                pass
        return results if results else [{"source": "OpenWeatherMap", "error": "API调用失败", "fetch_time": now.isoformat()}]

    async def collect(self) -> list[dict]:
        # Try QWeather first (faster in China), fallback to OpenWeatherMap
        results = await self.collect_from_qweather()
        if not results or "error" in results[0]:
            ow = await self.collect_from_openweather()
            results.extend(ow)
        return results
