"""Tests that run without an API key, a network connection or a model."""
import asyncio
import json
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

import agent_tool_calling as agent
import weather_client
from weather_api import app

OPENWEATHER_SAMPLE = {
    "name": "Paestum", "sys": {"country": "IT"},
    "main": {"temp": 21.3, "feels_like": 20.9, "humidity": 61},
    "weather": [{"description": "few clouds"}], "wind": {"speed": 3.4}, "dt": 1760000000,
}


def provider(status, payload=None):
    return httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(status, json=payload or {})))


def test_client_normalizes_provider_response(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test-key")
    monkeypatch.delenv("WEATHER_MOCK", raising=False)
    result = asyncio.run(weather_client.get_current_weather("Paestum", client=provider(200, OPENWEATHER_SAMPLE)))
    assert result["city"] == "Paestum" and result["temperature_c"] == 21.3
    assert result["description"] == "few clouds" and result["observed_at"].endswith("+00:00")


def test_client_error_mapping(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test-key")
    monkeypatch.delenv("WEATHER_MOCK", raising=False)
    with pytest.raises(weather_client.CityNotFound):
        asyncio.run(weather_client.get_current_weather("Nowhere", client=provider(404)))
    with pytest.raises(weather_client.WeatherError):
        asyncio.run(weather_client.get_current_weather("Paestum", client=provider(401)))


def test_missing_key_is_reported(monkeypatch):
    monkeypatch.delenv("OPENWEATHER_API_KEY", raising=False)
    monkeypatch.delenv("WEATHER_MOCK", raising=False)
    with pytest.raises(weather_client.MissingApiKey):
        asyncio.run(weather_client.get_current_weather("Paestum"))


def test_api_in_mock_mode(monkeypatch):
    monkeypatch.setenv("WEATHER_MOCK", "1")
    response = TestClient(app).get("/weather", params={"city": "paestum"})
    assert response.status_code == 200 and response.json()["city"] == "Paestum"


def test_api_status_codes(monkeypatch):
    monkeypatch.delenv("WEATHER_MOCK", raising=False)
    monkeypatch.delenv("OPENWEATHER_API_KEY", raising=False)
    http = TestClient(app)
    assert http.get("/weather", params={"city": "Paestum"}).status_code == 503
    assert http.get("/weather", params={"city": "x"}).status_code == 422
    assert http.get("/weather").status_code == 422


def test_openapi_describes_the_tool():
    operation = TestClient(app).get("/openapi.json").json()["paths"]["/weather"]["get"]
    assert operation["operationId"] == "get_current_weather" and "forecasts" in operation["description"]


def test_tool_argument_validation():
    assert "invalid arguments" in json.loads(agent.call_weather_tool('{"town": "x"}'))["error"]
    assert "invalid arguments" in json.loads(agent.call_weather_tool("not json"))["error"]


class FakeModel:
    """Stands in for the language model: first asks for the tool, then answers from its result."""

    def __init__(self):
        self.calls = 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            call = SimpleNamespace(id="c1", function=SimpleNamespace(name="get_current_weather", arguments='{"city": "Paestum"}'))
            message = SimpleNamespace(content=None, tool_calls=[call])
        else:
            tool_message = [m for m in kwargs["messages"] if m["role"] == "tool"][-1]
            message = SimpleNamespace(content="It is " + str(json.loads(tool_message["content"])["temperature_c"]) + " degrees.", tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_agent_loop_executes_tool_and_answers(monkeypatch):
    monkeypatch.setattr(agent, "call_weather_tool", lambda arguments: json.dumps({"temperature_c": 22.0}))
    monkeypatch.setitem(agent.EXECUTORS, "get_current_weather", agent.call_weather_tool)
    assert agent.run_agent(FakeModel(), "any-model", "Weather in Paestum?", verbose=False) == "It is 22.0 degrees."
