"""Weather from Open-Meteo (free, no key). Optional module."""
import json
from urllib.parse import urlencode

from .. import net

# WMO weather code -> icon key
def icon(code: int) -> str:
    if code in (0, 1):
        return "sun"
    if code == 2:
        return "partly"
    if code in (3,):
        return "cloud"
    if code in (45, 48):
        return "fog"
    if code in (71, 73, 75, 77, 85, 86):
        return "snow"
    if code in (95, 96, 99):
        return "storm"
    if code >= 51:
        return "rain"
    return "cloud"


WORDS = {"sun": "Sunny", "partly": "Partly cloudy", "cloud": "Cloudy", "fog": "Foggy", "snow": "Snow",
         "storm": "Thunderstorms", "rain": "Rain"}


def fetch(cfg: dict, tz: str) -> dict | None:
    """cfg = {place, lat, lon, units: 'fahrenheit'|'celsius'}"""
    f = cfg.get("units", "fahrenheit") == "fahrenheit"
    q = {"latitude": cfg["lat"], "longitude": cfg["lon"], "timezone": tz, "forecast_days": 2,
         "current": "temperature_2m,weather_code",
         "hourly": "temperature_2m,weather_code",
         "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max,weather_code",
         "temperature_unit": "fahrenheit" if f else "celsius", "wind_speed_unit": "mph" if f else "ms"}
    raw = net.get("https://api.open-meteo.com/v1/forecast?" + urlencode(q), 15)
    try:
        d = json.loads(raw)
    except Exception:
        return None
    cur, hr, day = d["current"], d["hourly"], d["daily"]
    now_i = next((i for i, t in enumerate(hr["time"]) if t >= cur["time"][:13]), 0)
    strip = [{"time": hr["time"][i][11:16], "temp": hr["temperature_2m"][i], "sym": icon(hr["weather_code"][i])}
             for i in range(now_i, min(now_i + 21, len(hr["time"])), 3)][:7]
    return {"place": cfg.get("place", ""), "temp": cur["temperature_2m"], "sym": icon(cur["weather_code"]),
            "hi": day["temperature_2m_max"][0], "lo": day["temperature_2m_min"][0],
            "rain": day["precipitation_probability_max"][0] or 0, "wind": day["wind_speed_10m_max"][0],
            "wind_unit": "mph" if f else "m/s", "strip": strip,
            "tomorrow": {"hi": day["temperature_2m_max"][1], "lo": day["temperature_2m_min"][1],
                         "sym": icon(day["weather_code"][1])}}


def headline(w: dict) -> str:
    word = WORDS[w["sym"]]
    return f"{word} and {round(w['hi'])}° in {w['place']}" if w["place"] else f"{word}, high of {round(w['hi'])}°"
