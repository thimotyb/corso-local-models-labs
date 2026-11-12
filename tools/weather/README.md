# Lab: a weather tool for a local model

Builds a tool step by step: from a mocked function to a real API wrapped with FastAPI, then the same tool as an MCP server, and finally a model that decides when to call it. The provider is [OpenWeather](https://openweathermap.org/api) (current weather API, free plan).

```
user question ──► local model ──proposes──► get_current_weather({"city": "Paestum"})
                       ▲                              │ validated and executed by the program
                       │ tool result (JSON)           ▼
                       └───────────── FastAPI service ──► OpenWeather API
```

## Files

| File | Role |
| --- | --- |
| `weather_client.py` | Calls OpenWeather, normalizes the answer (explicit units), maps errors. `WEATHER_MOCK=1` returns a canned answer. |
| `weather_api.py` | FastAPI wrapper: `GET /weather?city=...`, typed response, 404/422/502/503, OpenAPI at `/openapi.json`. |
| `weather_mcp.py` | The same tool as an MCP server (FastMCP). |
| `agent_tool_calling.py` | Tool-calling loop against a local model through an OpenAI-compatible endpoint (Ollama or a LiteLLM proxy). |
| `test_weather.py` | Tests that need no key, network or model. |

## Setup

From the repository root, with the virtual environment active:

```bash
pip install -r tools/weather/requirements.txt
cp .env.example .env     # then set OPENWEATHER_API_KEY, or use WEATHER_MOCK=1
cd tools/weather
python -m pytest -q      # 8 tests, no key needed
```

The model used by the agent must support tool calling (check the model page in the Ollama library for the "tools" capability). Chat model and endpoint are chosen with `CHAT_MODEL` and `LLM_BASE_URL`, so the same script runs against Ollama or a LiteLLM gateway.

## Steps

**1. Mocked tool.** Start the service without a key and call it:

```bash
WEATHER_MOCK=1 uvicorn weather_api:app --port 8000
curl "http://127.0.0.1:8000/weather?city=Paestum,IT"
```

Open http://127.0.0.1:8000/docs and read the generated documentation: the description of the operation is what a model will read.

**2. Real API.** Put your key in `.env`, restart without `WEATHER_MOCK`, and call a real city. Try an unknown city (404), a missing key (503) and a one-letter city (422). Note how each failure is reported as a clear message rather than a stack trace.

**3. Tool calling with a local model.**

```bash
python agent_tool_calling.py "Do I need a jacket in Paestum today?"
python agent_tool_calling.py "Who built the temples of Paestum?"   # should NOT call the tool
```

Read the printed steps: the model proposes a call, the program executes it, the model answers from the result. Then change `CHAT_MODEL` to a smaller or larger model and compare: does it call the tool when it should, and only then? Does it invent values when the tool fails (stop the API and ask again)?

**4. MCP variant.** Run `python weather_mcp.py`, open the MCP Inspector (`npx @modelcontextprotocol/inspector`), connect to `http://127.0.0.1:8020/weather-mcp` and call `get_weather_conditions`. The tool logic is the same; only the transport and the discovery mechanism change.

## What to observe

- The model never touches the network: it only writes a function name and JSON arguments. Validation and execution are the program's job.
- The quality of the tool description decides when a small model calls it.
- Errors must come back as data the model can read; otherwise it will make something up.
