"""A tool-calling loop against a local model, with the weather API as the tool.

The model never calls the API itself. It only proposes a call (a function name and JSON
arguments). This program validates the arguments, performs the HTTP request, and sends the
result back to the model, until the model answers in plain text.

Environment (all optional):
  LLM_BASE_URL   OpenAI-compatible endpoint: Ollama (default) or a LiteLLM proxy, e.g. http://localhost:4000/v1
  CHAT_MODEL     model name or LiteLLM logical name; it must support tool calling
  WEATHER_API_URL  base URL of the FastAPI service (default http://127.0.0.1:8000)

Run:  python agent_tool_calling.py "Do I need a jacket in Paestum today?"
"""
import json
import os
import sys

import httpx
from dotenv import find_dotenv, load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

load_dotenv(find_dotenv(usecwd=True))

WEATHER_API_URL = os.getenv("WEATHER_API_URL", "http://127.0.0.1:8000")
SYSTEM_PROMPT = (
    "You are a travel assistant. Use the get_current_weather tool only when the user asks about the "
    "current weather in a place. Never invent weather data: if the tool fails, say so. "
    "Answer briefly, in the language of the question."
)

TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": "Get the current weather conditions for a city given by name, optionally with a "
                       "country code (for example 'Paestum,IT'). Not for forecasts.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "City name, optionally followed by ',' and a country code"}},
            "required": ["city"],
            "additionalProperties": False,
        },
    },
}]


class WeatherArgs(BaseModel):
    city: str = Field(min_length=2, max_length=80)


def call_weather_tool(arguments: str) -> str:
    """Validate the model's arguments, call the API, and return a JSON string for the model."""
    try:
        args = WeatherArgs.model_validate_json(arguments)
    except ValidationError as exc:
        return json.dumps({"error": f"invalid arguments: {exc.errors()[0]['msg']}"})
    try:
        response = httpx.get(f"{WEATHER_API_URL}/weather", params={"city": args.city}, timeout=15)
    except httpx.HTTPError as exc:
        return json.dumps({"error": f"weather service unreachable: {exc}"})
    if response.status_code != 200:
        return json.dumps({"error": response.json().get("detail", f"HTTP {response.status_code}")})
    return response.text


EXECUTORS = {"get_current_weather": call_weather_tool}


def run_agent(client, model: str, question: str, max_steps: int = 5, verbose: bool = True) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}]
    for step in range(max_steps):
        reply = client.chat.completions.create(model=model, messages=messages, tools=TOOLS, temperature=0).choices[0].message
        if not reply.tool_calls:
            return reply.content or ""
        messages.append({"role": "assistant", "content": reply.content or "",
                         "tool_calls": [{"id": c.id, "type": "function",
                                         "function": {"name": c.function.name, "arguments": c.function.arguments}}
                                        for c in reply.tool_calls]})
        for call in reply.tool_calls:
            if verbose:
                print(f"[step {step + 1}] model requests {call.function.name}({call.function.arguments})")
            executor = EXECUTORS.get(call.function.name)
            result = executor(call.function.arguments) if executor else json.dumps({"error": "unknown tool"})
            if verbose:
                print(f"[step {step + 1}] tool result: {result[:200]}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    return "Stopped: too many tool-calling steps."


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What is the weather like in Paestum right now?"
    client = OpenAI(base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"), api_key=os.getenv("LLM_API_KEY", "not-needed-locally"))
    print(run_agent(client, os.getenv("CHAT_MODEL", "qwen3.5:9b"), question))
