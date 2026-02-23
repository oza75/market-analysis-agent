from __future__ import annotations

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from analyst_agent.utils import load_prompt

report_generator = LlmAgent(
    model=LiteLlm(model="openrouter/google/gemini-3-flash-preview"),
    name="report_generator",
    description=(
        "Formats the market analysis collected by the orchestrator into a structured markdown report. "
        "Called after all pricing, review, and trend data has been gathered."
    ),
    instruction=load_prompt("report_generator"),
    tools=[],
)
