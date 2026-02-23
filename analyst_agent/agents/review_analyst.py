from __future__ import annotations

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from analyst_agent.tools import web_search
from analyst_agent.utils import load_prompt

review_analyst = LlmAgent(
    model=LiteLlm(model="openrouter/google/gemini-3-flash-preview"),
    name="review_analyst",
    description=(
        "Retrieves and analyses client reviews for a given product and platform. "
        "Returns structured insights: overall sentiment, top praised and criticised aspects, "
        "value perception, and source URLs."
    ),
    instruction=load_prompt("review_analyst"),
    tools=[web_search],
)
