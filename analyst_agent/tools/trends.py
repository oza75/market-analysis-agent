from __future__ import annotations

import random
from datetime import date

from analyst_agent.tools.types import (
    PopularityTrendPoint,
    PopularityTrendResponse,
    PriceTrendPoint,
    PriceTrendResponse,
)
from analyst_agent.utils import iso_week_label

PRICE_CHANGE_THRESHOLD = 0.05
POPULARITY_CHANGE_THRESHOLD = 5


async def get_price_trend(product: str, weeks: int = 12) -> PriceTrendResponse:
    """
    Return a mock weekly price trend for a product.

    Parameters
    ----------
    product : str
        Product name to generate trend data for. Same name always produces the
        same data shape (deterministic seed).
    weeks : int, optional
        Number of weekly data points to return. Defaults to 12.

    Returns
    -------
    PriceTrendResponse
        Weekly price data points and overall trend direction.
    """
    rng = random.Random(hash(product))
    base_price = rng.uniform(50.0, 2000.0)
    today = date.today()

    data_points: list[PriceTrendPoint] = []
    price = base_price
    for i in range(weeks - 1, -1, -1):
        delta = rng.uniform(-0.04, 0.04) * price
        price = max(1.0, price + delta)
        data_points.append(
            PriceTrendPoint(week=iso_week_label(today, i), price_usd=round(price, 2))
        )

    first = data_points[0]["price_usd"]
    last = data_points[-1]["price_usd"]
    change_ratio = (last - first) / first

    if change_ratio > PRICE_CHANGE_THRESHOLD:
        trend = "increasing"
    elif change_ratio < -PRICE_CHANGE_THRESHOLD:
        trend = "decreasing"
    else:
        trend = "stable"

    return PriceTrendResponse(product=product, data_points=data_points, trend=trend)


async def get_popularity_trend(product: str, weeks: int = 12) -> PopularityTrendResponse:
    """
    Return a mock weekly popularity trend for a product.

    Parameters
    ----------
    product : str
        Product name to generate trend data for. Same name always produces the
        same data shape (deterministic seed).
    weeks : int, optional
        Number of weekly data points to return. Defaults to 12.

    Returns
    -------
    PopularityTrendResponse
        Weekly interest scores (0–100) and overall trend direction.
    """
    rng = random.Random(hash(product) + 1)
    today = date.today()

    data_points: list[PopularityTrendPoint] = []
    interest = rng.randint(30, 70)
    for i in range(weeks - 1, -1, -1):
        delta = rng.randint(-8, 8)
        interest = max(0, min(100, interest + delta))
        data_points.append(PopularityTrendPoint(week=iso_week_label(today, i), interest=interest))

    first = data_points[0]["interest"]
    last = data_points[-1]["interest"]
    diff = last - first

    if diff > POPULARITY_CHANGE_THRESHOLD:
        trend = "rising"
    elif diff < -POPULARITY_CHANGE_THRESHOLD:
        trend = "falling"
    else:
        trend = "stable"

    return PopularityTrendResponse(product=product, data_points=data_points, trend=trend)
