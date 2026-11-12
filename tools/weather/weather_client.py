"""Thin client for the OpenWeather "current weather" API.

Used by the FastAPI service (weather_api.py) and by the MCP server (weather_mcp.py), so the
logic that talks to the provider lives in exactly one place.

Set WEATHER_MOCK=1 to get a canned answer without any API key (step 1 of the lab).
"""
import os
from datetime import datetime, timezone

import httpx

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


class WeatherError(Exception):
    """The provider failed or returned something unusable."""


class CityNotFound(WeatherError):
    pass


class MissingApiKey(WeatherError):
    pass


def _mock(city: str) -> dict:
    return {
        "city": city.split(",")[0].strip().title(), "country": "XX", "temperature_c": 24.0, "feels_like_c": 24.5,
        "humidity_percent": 55, "description": "clear sky", "wind_speed_ms": 2.1,
        "observed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def _normalize(data: dict) -> dict:
    """Keep only the fields a model needs, with explicit units."""
    return {
        "city": data["name"],
        "country": data.get("sys", {}).get("country", ""),
        "temperature_c": data["main"]["temp"],
        "feels_like_c": data["main"].get("feels_like"),
        "humidity_percent": data["main"].get("humidity"),
        "description": data["weather"][0]["description"] if data.get("weather") else "",
        "wind_speed_ms": data.get("wind", {}).get("speed"),
        "observed_at": datetime.fromtimestamp(data["dt"], tz=timezone.utc).isoformat(timespec="seconds"),
    }


async def get_current_weather(city: str, client: httpx.AsyncClient | None = None) -> dict:
    if os.getenv("WEATHER_MOCK") == "1":
        return _mock(city)
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise MissingApiKey("OPENWEATHER_API_KEY is not set (or set WEATHER_MOCK=1)")
    params = {"q": city, "appid": api_key, "units": "metric"}
    own = client is None
    client = client or httpx.AsyncClient(timeout=10)
    try:
        response = await client.get(BASE_URL, params=params)
    except httpx.HTTPError as exc:
        raise WeatherError(f"weather provider unreachable: {exc}") from exc
    finally:
        if own:
            await client.aclose()
    if response.status_code == 404:
        raise CityNotFound(f"city not found: {city}")
    if response.status_code == 401:
        raise WeatherError("the provider rejected the API key (new keys can take some time to activate)")
    if response.status_code != 200:
        raise WeatherError(f"provider returned HTTP {response.status_code}")
    try:
        return _normalize(response.json())
    except (KeyError, IndexError, ValueError) as exc:
        raise WeatherError("unexpected response format from the provider") from exc
