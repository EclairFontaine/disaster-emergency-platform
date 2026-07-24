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
                    "latitude": city["lat"],
                    "longitude": city["lon"],
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
        results = await self.collect_from_qweather()
        if not results or "error" in results[0]:
            ow = await self.collect_from_openweather()
            results.extend(ow)
        return results

    async def collect_warnings(self) -> list[dict]:
        """采集天气预警 - 和风天气预警 + OpenWeatherMap极端天气检测"""
        now = datetime.now(timezone.utc)
        warnings = []

        # 1. 和风天气预警API
        from app.core.config import settings
        if settings.QWEATHER_API_KEY:
            for city in self.CITIES:
                try:
                    data = await self.fetch(
                        "https://devapi.qweather.com/v7/warning/now",
                        params={"location": city["qweather_id"], "key": settings.QWEATHER_API_KEY}
                    )
                    for w in data.get("warning", []):
                        warnings.append({
                            "source": "QWeather-Warning",
                            "city": city["name"],
                            "title": f"{city['name']}{w.get('typeName','')}{w.get('level','')}预警",
                            "type": w.get("type", ""),
                            "level": w.get("level", ""),
                            "text": w.get("text", ""),
                            "publish_time": w.get("pubTime", ""),
                            "latitude": city["lat"],
                            "longitude": city["lon"],
                            "fetch_time": now.isoformat(),
                        })
                except Exception:
                    pass

        # 2. OpenWeatherMap极端天气检测(5日预报)
        if settings.OPENWEATHER_API_KEY:
            for city in self.CITIES:
                try:
                    data = await self.fetch(
                        "https://api.openweathermap.org/data/2.5/forecast",
                        params={
                            "lat": city["lat"], "lon": city["lon"],
                            "appid": settings.OPENWEATHER_API_KEY,
                            "units": "metric", "lang": "zh_cn",
                            "cnt": 8,  # next 24 hours (3h intervals)
                        }
                    )
                    for item in data.get("list", []):
                        rain = item.get("rain", {}).get("3h", 0)
                        wind = item.get("wind", {}).get("speed", 0)
                        desc = item.get("weather", [{}])[0].get("description", "")
                        temp = item.get("main", {}).get("temp", 0)

                        if rain > 50:
                            warnings.append({
                                "source": "OWM-Forecast",
                                "city": city["name"],
                                "title": f"{city['name']}暴雨预警(预测降雨{rain}mm)",
                                "type": "rain",
                                "level": "暴雨",
                                "text": f"未来24小时预计降雨{rain}mm, 温度{temp}C",
                                "latitude": city["lat"], "longitude": city["lon"],
                                "fetch_time": now.isoformat(),
                            })
                        elif "暴雨" in desc or "暴雪" in desc or rain > 25:
                            warnings.append({
                                "source": "OWM-Forecast",
                                "city": city["name"],
                                "title": f"{city['name']}恶劣天气预警: {desc}",
                                "type": "weather",
                                "level": "橙色",
                                "text": f"预报: {desc}, 降雨{rain}mm, 风速{wind}m/s",
                                "latitude": city["lat"], "longitude": city["lon"],
                                "fetch_time": now.isoformat(),
                            })
                except Exception:
                    pass

        return warnings if warnings else [{"source": "Weather-Warnings", "error": "无预警", "fetch_time": now.isoformat()}]
