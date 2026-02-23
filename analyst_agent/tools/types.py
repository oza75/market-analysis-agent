from __future__ import annotations

from typing import Literal, TypedDict


class SearchResult(TypedDict):
    title: str
    url: str
    snippet: str


class WebSearchResponse(TypedDict):
    results: list[SearchResult]


class PriceTrendPoint(TypedDict):
    week: str
    price_usd: float


class PriceTrendResponse(TypedDict):
    product: str
    data_points: list[PriceTrendPoint]
    trend: Literal["increasing", "decreasing", "stable"]


class PopularityTrendPoint(TypedDict):
    week: str
    interest: int


class PopularityTrendResponse(TypedDict):
    product: str
    data_points: list[PopularityTrendPoint]
    trend: Literal["rising", "falling", "stable"]

