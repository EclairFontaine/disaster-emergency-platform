from datetime import datetime, timezone
from .base import BaseCollector


class WeatherCollector(BaseCollector):
    """气象数据采集 - 支持多个数据源"""

    def __init__(self):
        super().__init__(name="气象数据", url="", interval=1800)

    async def collect_from_nmc(self) -> list[dict]:
        """中央气象台(http://www.nmc.cn) 公开数据"""
        now = datetime.now(timezone.utc)
        try:
            data = await self.fetch(
                "https://devapi.qweather.com/v7/weather/now",
                params={
                    "location": "101290101",  # 昆明
                    "key": "YOUR_QWEATHER_KEY",
                }
            )
            return [{
                "source": "QWeather",
                "location": "昆明",
                "temperature": data.get("now", {}).get("temp"),
                "condition": data.get("now", {}).get("text"),
                "humidity": data.get("now", {}).get("humidity"),
                "wind": data.get("now", {}).get("windDir"),
                "fetch_time": now.isoformat(),
            }]
        except Exception:
            pass

        try:
            data = await self.fetch("http://www.nmc.cn/rest/weather", params={"stationid": "56778"})
            return [{
                "source": "NMC",
                "location": "昆明",
                "data": data,
                "fetch_time": now.isoformat(),
            }]
        except Exception as e:
            return [{"source": "NMC", "error": str(e), "fetch_time": now.isoformat()}]

    async def collect_from_openweather(self) -> list[dict]:
        """OpenWeatherMap免费API"""
        now = datetime.now(timezone.utc)
        cities = [
            {"name": "昆明", "lat": 25.04, "lon": 102.68},
            {"name": "大理", "lat": 25.59, "lon": 100.23},
            {"name": "丽江", "lat": 26.87, "lon": 100.23},
            {"name": "昭通", "lat": 27.34, "lon": 103.72},
            {"name": "普洱", "lat": 22.78, "lon": 100.97},
        ]
        results = []
        for city in cities:
            try:
                data = await self.fetch(
                    "https://api.openweathermap.org/data/2.5/weather",
                    params={
                        "lat": city["lat"],
                        "lon": city["lon"],
                        "appid": "YOUR_OPENWEATHER_KEY",
                        "units": "metric",
                        "lang": "zh_cn",
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
        results = await self.collect_from_openweather()
        if not results or "error" in results[0]:
            nmc = await self.collect_from_nmc()
            results.extend(nmc)
        return results
