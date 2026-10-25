import time
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# WMO Weather interpretation codes
WMO_CODES = {
    0: ("Clear Sky", "clear"),
    1: ("Mainly Clear", "partly-cloudy"),
    2: ("Partly Cloudy", "partly-cloudy"),
    3: ("Overcast", "cloudy"),
    45: ("Fog", "fog"),
    48: ("Depositing Rime Fog", "fog"),
    51: ("Light Drizzle", "drizzle"),
    53: ("Moderate Drizzle", "drizzle"),
    55: ("Dense Drizzle", "drizzle"),
    61: ("Slight Rain", "rain"),
    63: ("Moderate Rain", "rain"),
    65: ("Heavy Rain", "rain"),
    71: ("Slight Snow", "snow"),
    73: ("Moderate Snow", "snow"),
    75: ("Heavy Snow", "snow"),
    80: ("Slight Rain Showers", "rain"),
    81: ("Moderate Rain Showers", "rain"),
    82: ("Violent Rain Showers", "rain"),
    95: ("Thunderstorm", "thunderstorm"),
    96: ("Thunderstorm with Hail", "thunderstorm"),
    99: ("Thunderstorm with Heavy Hail", "thunderstorm"),
}


class WeatherService:
    # Ormond, Melbourne, Victoria, Australia
    ORMOND_LAT = -37.8992
    ORMOND_LON = 145.0392
    TIMEZONE = "Australia/Melbourne"
    CACHE_TTL_SECONDS = 600  # 10 minutes

    def __init__(self):
        self.last_update_time: Optional[float] = None
        self.cached_weather: Optional[Dict[str, Any]] = None

    def _get_description_and_icon(self, code: int) -> tuple[str, str]:
        return WMO_CODES.get(code, ("Unknown", "partly-cloudy"))

    def _get_mock_weather(self) -> Dict[str, Any]:
        """Fallback realistic weather for Ormond, Melbourne."""
        return {
            "stale": True,
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "location": "Ormond, VIC",
            "current": {
                "temperature": 18.5,
                "feels_like": 17.8,
                "condition": "Partly Cloudy",
                "icon": "partly-cloudy",
                "high": 21.0,
                "low": 12.0,
                "precipitation_chance": 10,
                "wind_speed": 18.5,
                "wind_direction": 210,
                "humidity": 62,
                "weather_code": 2
            },
            "hourly": [
                {"time": "14:00", "temp": 19.5, "precip_prob": 10, "icon": "partly-cloudy"},
                {"time": "15:00", "temp": 20.2, "precip_prob": 10, "icon": "partly-cloudy"},
                {"time": "16:00", "temp": 20.8, "precip_prob": 5, "icon": "clear"},
                {"time": "17:00", "temp": 20.1, "precip_prob": 5, "icon": "clear"},
                {"time": "18:00", "temp": 18.9, "precip_prob": 10, "icon": "clear"},
                {"time": "19:00", "temp": 17.5, "precip_prob": 15, "icon": "partly-cloudy"},
                {"time": "20:00", "temp": 16.2, "precip_prob": 15, "icon": "partly-cloudy"},
            ],
            "daily": [
                {"day": "Today", "high": 21.0, "low": 12.0, "condition": "Partly Cloudy", "icon": "partly-cloudy", "precip_prob": 10},
                {"day": "Tomorrow", "high": 23.0, "low": 13.5, "condition": "Sunny", "icon": "clear", "precip_prob": 0},
                {"day": "Wed", "high": 19.0, "low": 11.0, "condition": "Slight Rain", "icon": "rain", "precip_prob": 60},
                {"day": "Thu", "high": 22.0, "low": 12.5, "condition": "Partly Cloudy", "icon": "partly-cloudy", "precip_prob": 20},
                {"day": "Fri", "high": 25.5, "low": 14.0, "condition": "Sunny", "icon": "clear", "precip_prob": 5},
            ]
        }

    def get_weather(self) -> Dict[str, Any]:
        now = time.time()
        if self.cached_weather and self.last_update_time and (now - self.last_update_time < self.CACHE_TTL_SECONDS):
            return self.cached_weather

        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={self.ORMOND_LAT}&longitude={self.ORMOND_LON}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m"
            f"&hourly=temperature_2m,precipitation_probability,weather_code"
            f"&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
            f"&timezone={self.TIMEZONE.replace('/', '%2F')}"
        )

        try:
            resp = requests.get(url, timeout=6.0)
            if resp.status_code == 200:
                data = resp.json()
                current_raw = data.get("current", {})
                daily_raw = data.get("daily", {})
                hourly_raw = data.get("hourly", {})

                cond_text, icon = self._get_description_and_icon(current_raw.get("weather_code", 0))

                # Today high and low
                today_high = daily_raw.get("temperature_2m_max", [None])[0]
                today_low = daily_raw.get("temperature_2m_min", [None])[0]
                today_precip = daily_raw.get("precipitation_probability_max", [0])[0]

                # Hourly forecast (next 8 hours)
                hourly = []
                times = hourly_raw.get("time", [])
                temps = hourly_raw.get("temperature_2m", [])
                probs = hourly_raw.get("precipitation_probability", [])
                codes = hourly_raw.get("weather_code", [])

                # Find current index
                curr_iso = current_raw.get("time", "")
                start_idx = 0
                if curr_iso and curr_iso in times:
                    start_idx = times.index(curr_iso)

                for i in range(start_idx, min(start_idx + 8, len(times))):
                    h_time = times[i].split("T")[-1] if "T" in times[i] else times[i]
                    _, h_icon = self._get_description_and_icon(codes[i] if i < len(codes) else 0)
                    hourly.append({
                        "time": h_time,
                        "temp": round(temps[i], 1) if i < len(temps) else 0,
                        "precip_prob": probs[i] if i < len(probs) else 0,
                        "icon": h_icon
                    })

                # Daily forecast
                daily = []
                d_times = daily_raw.get("time", [])
                d_maxs = daily_raw.get("temperature_2m_max", [])
                d_mins = daily_raw.get("temperature_2m_min", [])
                d_codes = daily_raw.get("weather_code", [])
                d_probs = daily_raw.get("precipitation_probability_max", [])

                days_map = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                for i in range(min(6, len(d_times))):
                    d_cond, d_icon = self._get_description_and_icon(d_codes[i] if i < len(d_codes) else 0)
                    day_label = "Today" if i == 0 else ("Tomorrow" if i == 1 else d_times[i])
                    # Parse day of week if date formatted YYYY-MM-DD
                    if i >= 2 and "-" in d_times[i]:
                        try:
                            import datetime
                            dt = datetime.datetime.strptime(d_times[i], "%Y-%m-%d")
                            day_label = days_map[dt.weekday()]
                        except Exception:
                            pass

                    daily.append({
                        "day": day_label,
                        "high": round(d_maxs[i], 1) if i < len(d_maxs) else None,
                        "low": round(d_mins[i], 1) if i < len(d_mins) else None,
                        "condition": d_cond,
                        "icon": d_icon,
                        "precip_prob": d_probs[i] if i < len(d_probs) else 0
                    })

                parsed_weather = {
                    "stale": False,
                    "last_updated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "location": "Ormond, VIC",
                    "current": {
                        "temperature": round(current_raw.get("temperature_2m", 0), 1),
                        "feels_like": round(current_raw.get("apparent_temperature", 0), 1),
                        "condition": cond_text,
                        "icon": icon,
                        "high": round(today_high, 1) if today_high is not None else None,
                        "low": round(today_low, 1) if today_low is not None else None,
                        "precipitation_chance": today_precip,
                        "wind_speed": round(current_raw.get("wind_speed_10m", 0), 1),
                        "wind_direction": current_raw.get("wind_direction_10m", 0),
                        "humidity": current_raw.get("relative_humidity_2m", 0),
                        "weather_code": current_raw.get("weather_code", 0)
                    },
                    "hourly": hourly,
                    "daily": daily
                }

                self.cached_weather = parsed_weather
                self.last_update_time = now
                return parsed_weather

        except Exception as e:
            logger.warning(f"Error fetching Open-Meteo weather: {e}")

        if self.cached_weather:
            self.cached_weather["stale"] = True
            return self.cached_weather

        return self._get_mock_weather()
