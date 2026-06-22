import json
import time
import urllib.request
import socket
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List


GEO_API = "http://ip-api.com/json/"
WEATHER_API = "https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
NEWS_API = "https://newsapi.org/v2/top-headlines?country={country}&pageSize=5&apiKey={key}"
TIME_API = "http://worldtimeapi.org/api/ip"


class GodsEye:
    def __init__(self):
        self._location_cache = None
        self._weather_cache = None
        self._news_cache = None
        self._last_geo_time = 0
        self._last_weather_time = 0
        self._last_news_time = 0
        self._cache_ttl = 300
        self._news_api_key = ""
        self._stats = {"geo_lookups": 0, "weather_lookups": 0, "time_lookups": 0, "errors": 0}

    def _cached_or_fresh(self, cache_key: str, ttl: int = None) -> bool:
        ttl = ttl or self._cache_ttl
        last_time = getattr(self, f"_last_{cache_key}_time", 0)
        return (time.time() - last_time) < ttl

    def get_location(self, force: bool = False) -> Dict[str, Any]:
        if not force and self._location_cache and self._cached_or_fresh("geo"):
            return self._location_cache
        try:
            resp = urllib.request.urlopen(GEO_API, timeout=10)
            data = json.loads(resp.read())
            if data.get("status") == "success":
                self._location_cache = {
                    "city": data.get("city", "Unknown"),
                    "region": data.get("regionName", ""),
                    "country": data.get("country", "Unknown"),
                    "country_code": data.get("countryCode", ""),
                    "lat": data.get("lat", 0.0),
                    "lon": data.get("lon", 0.0),
                    "timezone": data.get("timezone", "UTC"),
                    "isp": data.get("isp", ""),
                    "ip": data.get("query", ""),
                    "source": "ip-api.com",
                }
                self._last_geo_time = time.time()
                self._stats["geo_lookups"] += 1
        except Exception:
            self._stats["errors"] += 1
            if not self._location_cache:
                self._location_cache = {
                    "city": "Unknown", "country": "Unknown",
                    "lat": 0.0, "lon": 0.0, "timezone": "UTC",
                    "source": "default",
                }
        return self._location_cache

    def get_weather(self, force: bool = False) -> Dict[str, Any]:
        if not force and self._weather_cache and self._cached_or_fresh("weather"):
            return self._weather_cache
        loc = self.get_location()
        lat, lon = loc.get("lat", 0), loc.get("lon", 0)
        if not lat and not lon:
            return {"error": "No location available"}
        try:
            url = WEATHER_API.format(lat=lat, lon=lon)
            resp = urllib.request.urlopen(url, timeout=10)
            data = json.loads(resp.read())
            cw = data.get("current_weather", {})
            wmo = cw.get("weathercode", 0)
            weather_desc = self._wmo_code(wmo)
            self._weather_cache = {
                "temperature_c": cw.get("temperature"),
                "wind_speed_kmh": cw.get("windspeed"),
                "wind_direction": cw.get("winddirection"),
                "weather_code": wmo,
                "weather_description": weather_desc,
                "is_day": bool(cw.get("is_day", 1)),
                "elevation_m": data.get("elevation", 0),
                "time": cw.get("time", ""),
                "source": "open-meteo.com",
            }
            self._last_weather_time = time.time()
            self._stats["weather_lookups"] += 1
        except Exception:
            self._stats["errors"] += 1
            if not self._weather_cache:
                self._weather_cache = {"error": "Weather fetch failed"}
        return self._weather_cache

    def get_time(self) -> Dict[str, Any]:
        self._stats["time_lookups"] += 1
        now = datetime.now(timezone.utc)
        loc = self.get_location()
        tz = loc.get("timezone", "UTC")
        return {
            "utc": now.isoformat(),
            "timestamp": now.timestamp(),
            "timezone": tz,
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "hour": now.hour,
            "minute": now.minute,
            "weekday": now.strftime("%A"),
            "source": "system",
        }

    def get_top_news(self, force: bool = False) -> List[Dict[str, Any]]:
        if not force and self._news_cache and self._cached_or_fresh("news", 600):
            return self._news_cache
        if not self._news_api_key:
            self._news_cache = []
            return []
        loc = self.get_location()
        cc = loc.get("country_code", "us").lower()
        try:
            url = NEWS_API.format(country=cc, key=self._news_api_key)
            resp = urllib.request.urlopen(url, timeout=10)
            data = json.loads(resp.read())
            articles = data.get("articles", [])
            self._news_cache = [
                {
                    "title": a.get("title", ""),
                    "source": a.get("source", {}).get("name", ""),
                    "url": a.get("url", ""),
                }
                for a in articles[:5]
            ]
            self._last_news_time = time.time()
        except Exception:
            self._stats["errors"] += 1
            self._news_cache = []
        return self._news_cache

    def scan_network(self) -> Dict[str, Any]:
        hostname = socket.gethostname()
        local_ip = "127.0.0.1"
        try:
            local_ip = socket.gethostbyname(hostname)
        except Exception:
            pass
        return {
            "hostname": hostname,
            "local_ip": local_ip,
        }

    def get_situational_awareness(self) -> Dict[str, Any]:
        loc = self.get_location()
        weather = self.get_weather()
        t = self.get_time()
        net = self.scan_network()
        awareness = {
            "location": loc,
            "weather": weather,
            "time": t,
            "network": net,
            "timestamp": time.time(),
        }
        return awareness

    def report(self) -> str:
        sa = self.get_situational_awareness()
        loc = sa["location"]
        weather = sa["weather"]
        t = sa["time"]
        net = sa["network"]
        lines = [
            f"Location: {loc.get('city', '?')}, {loc.get('country', '?')} ({loc.get('lat', '?')}, {loc.get('lon', '?')})",
            f"Timezone: {loc.get('timezone', '?')}",
            f"Time: {t['year']}-{t['month']:02d}-{t['day']:02d} {t['hour']:02d}:{t['minute']:02d} ({t['weekday']})",
        ]
        if isinstance(weather, dict) and "temperature_c" in weather:
            desc = weather.get("weather_description", "unknown")
            lines.append(f"Weather: {weather['temperature_c']}C, wind {weather['wind_speed_kmh']} km/h, {desc}")
        lines.append(f"Network: {net.get('hostname', '?')} ({net.get('local_ip', '?')})")
        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "geo_lookups": self._stats["geo_lookups"],
            "weather_lookups": self._stats["weather_lookups"],
            "time_lookups": self._stats["time_lookups"],
            "errors": self._stats["errors"],
            "location_cached": self._location_cache is not None,
            "weather_cached": self._weather_cache is not None,
        }

    @staticmethod
    def _wmo_code(code: int) -> str:
        codes = {
            0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
            45: "foggy", 48: "depositing rime fog", 51: "light drizzle", 53: "moderate drizzle",
            55: "dense drizzle", 56: "light freezing drizzle", 57: "dense freezing drizzle",
            61: "slight rain", 63: "moderate rain", 65: "heavy rain",
            66: "light freezing rain", 67: "heavy freezing rain",
            71: "slight snow", 73: "moderate snow", 75: "heavy snow",
            77: "snow grains", 80: "slight rain showers", 81: "moderate rain showers",
            82: "violent rain showers", 85: "slight snow showers", 86: "heavy snow showers",
            95: "thunderstorm", 96: "thunderstorm with slight hail", 99: "thunderstorm with heavy hail",
        }
        return codes.get(code, f"code {code}")

    def save(self) -> dict:
        return {"stats": self._stats}

    def load(self, data: dict):
        self._stats = data.get("stats", {"geo_lookups": 0, "weather_lookups": 0, "time_lookups": 0, "errors": 0})
