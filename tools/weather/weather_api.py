"""FastAPI service that wraps the OpenWeather current-weather API as a small, well-described tool API.

Run:  uvicorn weather_api:app --port 8000
Docs: http://127.0.0.1:8000/docs  (interactive)   http://127.0.0.1:8000/openapi.json (machine-readable)
"""
from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from weather_client import CityNotFound, MissingApiKey, WeatherError, get_current_weather

load_dotenv(find_dotenv(usecwd=True))

app = FastAPI(
    title="Weather tool API",
    version="1.0.0",
    description="Current weather for a city, normalized for use as a tool by language models.",
)


class Weather(BaseModel):
    city: str = Field(description="Name of the city as resolved by the provider")
    country: str = Field(description="ISO 3166 country code")
    temperature_c: float = Field(description="Air temperature in degrees Celsius")
    feels_like_c: float | None = Field(default=None, description="Perceived temperature in degrees Celsius")
    humidity_percent: int | None = Field(default=None, description="Relative humidity, 0-100")
    description: str = Field(description="Short text description of the conditions")
    wind_speed_ms: float | None = Field(default=None, description="Wind speed in metres per second")
    observed_at: str = Field(description="Observation time, ISO 8601, UTC")


@app.get("/health", include_in_schema=False)
async def health() -> dict:
    return {"status": "ok"}


@app.get(
    "/weather",
    response_model=Weather,
    operation_id="get_current_weather",
    summary="Get the current weather for a city",
    description="Returns the current conditions for a city given by name, optionally with a country code "
                "(for example 'Paestum' or 'Paestum,IT'). Use it only when the user asks for current "
                "weather conditions, not for forecasts or climate information.",
)
async def current_weather(
    city: str = Query(..., min_length=2, max_length=80, description="City name, optionally followed by ',' and a country code",
                      examples=["Paestum,IT"]),
) -> dict:
    try:
        return await get_current_weather(city)
    except CityNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except MissingApiKey as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except WeatherError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
