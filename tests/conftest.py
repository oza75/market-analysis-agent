from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

import analyst_agent.tools.search as search_module


@pytest.fixture(autouse=True)
def clear_search_cache():
    """Clear the search cache before and after every test."""
    search_module.search_cache.clear()
    yield
    search_module.search_cache.clear()


@pytest.fixture
def mock_tavily(monkeypatch):
    """
    Replace the module-level Tavily client with a mock.

    Returns the mock client so tests can assert on call args and count.
    """
    client = MagicMock()
    client.search = AsyncMock(return_value={
        "results": [
            {"title": "iPhone 16 Pro", "url": "https://amazon.com/iphone", "content": "Price: $999"}
        ]
    })
    monkeypatch.setattr(search_module, "tavily_client", client)
    return client
