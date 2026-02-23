from __future__ import annotations

import pytest
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types

load_dotenv("analyst_agent/.env")

from analyst_agent.agents.trend_analyzer import trend_analyzer  # noqa: E402

USER_QUERY = "Analyse price and popularity trends for iPhone 16 Pro"


async def run_trend_agent(callback, session_id: str) -> str | None:
    """Run trend_analyzer with a before_tool_callback and return the final response text."""
    agent = trend_analyzer.model_copy(update={"before_tool_callback": callback})
    runner = InMemoryRunner(agent=agent)
    runner.auto_create_session = True

    final_text: str | None = None
    async for event in runner.run_async(
        user_id="test",
        session_id=session_id,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text=USER_QUERY)],
        ),
    ):
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text:
                    final_text = part.text
    return final_text


def test_trend_analyzer_registers_tools():
    """Both get_price_trend and get_popularity_trend must be registered as tools."""
    tool_names = [t.__name__ for t in trend_analyzer.tools]
    assert "get_price_trend" in tool_names
    assert "get_popularity_trend" in tool_names


@pytest.mark.integration
async def test_trend_analyzer_invokes_both_tools():
    """trend_analyzer must call both get_price_trend and get_popularity_trend."""
    called_tools: set[str] = set()

    def track(tool, args, tool_context):
        called_tools.add(tool.name)
        return None

    await run_trend_agent(track, "test-trend-invokes-both")

    assert "get_price_trend" in called_tools
    assert "get_popularity_trend" in called_tools


@pytest.mark.integration
async def test_trend_analyzer_handles_tool_failure():
    """trend_analyzer must still produce a response when tools return errors."""
    def simulate_failure(tool, args, tool_context):
        return {"error": f"{tool.name} is unavailable."}

    final_text = await run_trend_agent(simulate_failure, "test-trend-tool-failure")

    assert final_text is not None
