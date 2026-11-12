"""The same weather tool exposed as an MCP server with FastMCP (compare with the REST API in weather_api.py).

Run:  python weather_mcp.py        (serves http://127.0.0.1:8020/weather-mcp)
Test: npx @modelcontextprotocol/inspector   and connect to the URL above.
"""
from dotenv import find_dotenv, load_dotenv
from fastmcp import FastMCP

from weather_client import get_current_weather

load_dotenv(find_dotenv(usecwd=True))

mcp = FastMCP("mcp-openweather")


@mcp.tool(description="Get the current weather conditions for a city given by name, optionally with a "
                      "country code (for example 'Paestum,IT'). Not for forecasts.")
async def get_weather_conditions(city: str) -> dict:
    return await get_current_weather(city)


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8020, path="/weather-mcp")
