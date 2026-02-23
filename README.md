# market-analyst-agent

The pricing agent uses OpenRouter and a Tavily-based function tool for web search; it only answers pricing-related questions. Set `OPENROUTER_API_KEY` and `TAVILY_API_KEY` in `analyst_agent/.env`. Run via `docker compose run --rm --env-file analyst_agent/.env app adk run analyst_agent` or `docker compose run --rm --service-ports --env-file analyst_agent/.env app adk web`.
