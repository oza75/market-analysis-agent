from __future__ import annotations

import pytest
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types

load_dotenv("analyst_agent/.env")

from analyst_agent.agents.review_analyst import review_analyst  # noqa: E402

USER_QUERY = "Analyse reviews for iPhone 16 Pro on Amazon"

MOCK_SEARCH_RESULT = {
    "results": [
        {
            "title": "iPhone 16 Pro Reddit: Real buyer opinions",
            "url": "https://reddit.com/r/iphone/comments/test",
            "snippet": "Great camera, battery lasts all day. Pricey but worth it.",
        }
    ]
}


async def run_review_agent(callback, session_id: str) -> str | None:
    """Run review_analyst with a before_tool_callback and return the final response text."""
    agent = review_analyst.model_copy(update={"before_tool_callback": callback})
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


def test_review_analyst_registers_web_search():
    """web_search must be registered as a tool — removing it silently breaks the agent."""
    tool_names = [t.__name__ for t in review_analyst.tools]
    assert "web_search" in tool_names


@pytest.mark.integration
async def test_review_analyst_invokes_web_search():
    """review_analyst must call web_search at least once with a non-empty query."""
    tracked_calls: list[dict] = []

    def track_and_mock(tool, args, tool_context):
        if tool.name == "web_search":
            tracked_calls.append(args)
            return MOCK_SEARCH_RESULT
        return None

    await run_review_agent(track_and_mock, "test-review-calls-web-search")

    assert len(tracked_calls) >= 1, "review_analyst must call web_search at least once"
    assert "query" in tracked_calls[0]
    assert len(tracked_calls[0]["query"]) > 0


@pytest.mark.integration
async def test_review_analyst_handles_web_search_failure():
    """review_analyst must still produce a response when web_search returns an error."""
    def simulate_failure(tool, args, tool_context):
        if tool.name == "web_search":
            return {"error": "Search service unavailable. Cannot retrieve reviews."}
        return None

    final_text = await run_review_agent(simulate_failure, "test-review-web-search-failure")

    assert final_text is not None, "Agent must produce a response even when web_search fails"
