from __future__ import annotations

import pytest
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types

load_dotenv("analyst_agent/.env")

from analyst_agent.agent import root_agent  # noqa: E402

PRICING_QUERY = "Find prices for iPhone 16 Pro on Amazon, Walmart and Best Buy"
UNRELATED_QUERY = "What is the weather in Paris today?"

MOCK_WEB_SEARCH = {
    "results": [
        {"title": "iPhone 16 Pro - Amazon", "url": "https://amazon.com/iphone", "snippet": "$999"},
        {"title": "iPhone 16 Pro - Walmart", "url": "https://walmart.com/iphone", "snippet": "$989"},
    ]
}
MOCK_REVIEW_RESPONSE = (
    "Product insights: Excellent camera quality, praised battery life. "
    "Platform insights: Amazon offers fast shipping with reliable packaging."
)
MOCK_TREND_RESPONSE = (
    "Price trend: stable. Popularity trend: rising. Recommendation: Good time to buy."
)


async def run_market_agent(callback, session_id: str, query: str = PRICING_QUERY) -> str | None:
    """Run market_analyst_agent with a before_tool_callback and return the final response text."""
    agent = root_agent.model_copy(update={"before_tool_callback": callback})
    runner = InMemoryRunner(agent=agent)
    runner.auto_create_session = True

    final_text: str | None = None
    async for event in runner.run_async(
        user_id="test",
        session_id=session_id,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text=query)],
        ),
    ):
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text:
                    final_text = part.text
    return final_text


def test_market_analyst_registers_all_tools():
    """All tools and sub-agents must be registered — missing any silently breaks orchestration."""
    tool_names = [getattr(t, "name", None) or t.__name__ for t in root_agent.tools]
    assert "web_search" in tool_names
    assert "review_analyst" in tool_names
    assert "trend_analyzer" in tool_names

    sub_agent_names = [a.name for a in root_agent.sub_agents]
    assert "report_generator" in sub_agent_names


@pytest.mark.integration
async def test_market_analyst_rejects_unrelated_request():
    """Requests unrelated to market analysis must not trigger any tool call."""
    called_tools: list[str] = []

    def track(tool, args, tool_context):
        called_tools.append(tool.name)
        return None

    await run_market_agent(track, "test-market-unrelated", query=UNRELATED_QUERY)

    assert len(called_tools) == 0, f"No tools should be called for unrelated requests, got: {called_tools}"


@pytest.mark.integration
async def test_market_analyst_calls_web_search_for_pricing():
    """market_analyst_agent must call web_search when asked to find product prices."""
    called_tools: list[str] = []

    def track_and_mock(tool, args, tool_context):
        called_tools.append(tool.name)
        if tool.name == "web_search":
            return MOCK_WEB_SEARCH
        if tool.name == "review_analyst":
            return MOCK_REVIEW_RESPONSE
        if tool.name == "trend_analyzer":
            return MOCK_TREND_RESPONSE
        return None

    await run_market_agent(track_and_mock, "test-market-calls-web-search")

    assert "web_search" in called_tools
