from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

import analyst_agent.tools.search as search_module
from analyst_agent.tools.search import web_search


async def test_cache_hit_skips_tavily(mock_tavily):
    """A second call with identical args must not reach the Tavily API.

    The cache key is (query, max_results). On a hit the cached response is
    returned immediately.
    """
    await web_search("iphone 16 pro price")
    await web_search("iphone 16 pro price")

    assert mock_tavily.search.call_count == 1


async def test_include_domains_forwarded_to_tavily(mock_tavily):
    """include_domains must be forwarded to the Tavily search call.

    If dropped silently, domain-restricted searches (e.g. amazon.com only)
    would return results from any domain — breaking the pricing workflow.
    """
    await web_search("iphone 16 pro price", include_domains=["amazon.com"])

    call_kwargs = mock_tavily.search.call_args.kwargs
    assert call_kwargs.get("include_domains") == ["amazon.com"]


async def test_tenacity_retries_three_times_on_failure(monkeypatch):
    """When Tavily consistently fails, the function must retry exactly 3 times.

    The @retry decorator is configured with stop_after_attempt(3) and
    reraise=True.
    """
    failing_client_mock = AsyncMock()
    failing_client_mock.search = AsyncMock(side_effect=Exception("Tavily unavailable"))
    monkeypatch.setattr(search_module, "tavily_client", failing_client_mock)

    with pytest.raises(Exception):
        await web_search("iphone 16 pro price")

    assert failing_client_mock.search.call_count == 3
