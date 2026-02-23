from __future__ import annotations

import pytest

from analyst_agent.tools.trends import get_popularity_trend, get_price_trend


async def test_trend_tools_are_deterministic():
    """Same product name must always return identical data for both tools.

    Both tools seed random.Random from hash(product). If the seed is ever
    removed or changed, results become non-deterministic and the LLM receives
    different trend data on every invocation.
    """
    price_a = await get_price_trend("iPhone 16 Pro")
    price_b = await get_price_trend("iPhone 16 Pro")
    assert price_a == price_b

    popularity_a = await get_popularity_trend("iPhone 16 Pro")
    popularity_b = await get_popularity_trend("iPhone 16 Pro")
    assert popularity_a == popularity_b


async def test_trend_tools_respect_weeks_parameter():
    """
    The weeks parameter must control the exact number of data points returned.
    """
    price = await get_price_trend("Macbook Pro", weeks=6)
    assert len(price["data_points"]) == 6

    popularity = await get_popularity_trend("Macbook Pro", weeks=6)
    assert len(popularity["data_points"]) == 6