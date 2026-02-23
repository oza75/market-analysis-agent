from __future__ import annotations

from analyst_agent.config import config
from analyst_agent.tools.types import SearchResult, WebSearchResponse
from cachetools import TTLCache
from tavily import AsyncTavilyClient
from tenacity import retry, stop_after_attempt

tavily_client = (
    AsyncTavilyClient(api_key=config.TAVILY_API_KEY)
    if config.TAVILY_API_KEY
    else None
)

# Cache search results for 30 minutes
search_cache: TTLCache[tuple[str, int], WebSearchResponse] = TTLCache(
    maxsize=128, ttl=1800
)


@retry(stop=stop_after_attempt(3), reraise=True)
async def web_search(query: str, max_results: int = 10, include_domains: list[str] = None) -> WebSearchResponse:
    """
    Run a web search and return results (title, url, snippet).

    Parameters
    ----------
    query : str
        The search query (e.g. product name, "price amazon walmart").
    max_results : int, optional
        Maximum number of results to return. Defaults to 10.
    include_domains : list[str], optional
        List of domains to include in the search. Defaults to None.
    Returns
    -------
    WebSearchResponse: list of SearchResult
    """
    key = (query, max_results)
    if key in search_cache:
        return search_cache[key]

    if tavily_client is None:
       raise Exception("TAVILY_API_KEY is not set.")

    try:
        response = await tavily_client.search(
            query=query, max_results=max_results, include_domains=include_domains
        )
    except Exception as e:
        raise Exception(f"Error while searching the web: {str(e)}") from e

    raw_results = response.get("results", [])
    response = WebSearchResponse(results=[
        SearchResult(
            title=r.get("title", ""),
            url=r.get("url", ""),
            snippet=r.get("content", ""),
        )
        for r in raw_results
    ])
    
    search_cache[key] = response
    return response
