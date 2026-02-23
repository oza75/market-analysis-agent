from __future__ import annotations

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from analyst_agent.tools import get_popularity_trend, get_price_trend
from analyst_agent.utils import load_prompt

trend_analyzer = LlmAgent(
    model=LiteLlm(model="openrouter/google/gemini-3-flash-preview"),
    name="trend_analyzer",
    description=(
        "Analyses price and popularity trends for a product over time. "
        "Returns trend direction, data-backed evidence, and a timing recommendation. "
        "Called once per product."
    ),
    instruction=load_prompt("trend_analyzer"),
    tools=[get_price_trend, get_popularity_trend],
)
