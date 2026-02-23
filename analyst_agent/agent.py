from __future__ import annotations

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.agent_tool import AgentTool

from analyst_agent.agents import report_generator, review_analyst, trend_analyzer
from analyst_agent.tools import web_search
from analyst_agent.utils import load_prompt

root_agent = LlmAgent(
    model=LiteLlm(model="openrouter/google/gemini-3-flash-preview"),
    name="market_analyst_agent",
    description="You are a market analyst assistant. Your sole purpose is to analyze a product's market presence and pricing across retail platforms.",
    instruction=load_prompt("orchestrator"),
    tools=[web_search, AgentTool(agent=review_analyst), AgentTool(agent=trend_analyzer)],
    sub_agents=[report_generator],
)
