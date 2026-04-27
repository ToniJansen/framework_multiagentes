from __future__ import annotations

import os

from langchain_core.tools import tool

from agentkit.guardrails.middleware import wrap_tool_call


@tool
@wrap_tool_call()
def web_search(query: str, max_results: int = 3) -> str:
    """Search the web using Tavily and return a summary of top results.

    Requires TAVILY_API_KEY in environment.
    """
    from tavily import TavilyClient

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "TAVILY_API_KEY not set — web search unavailable."

    client = TavilyClient(api_key=api_key)
    response = client.search(query=query, max_results=max_results)
    results = response.get("results", [])

    if not results:
        return "(no results)"

    lines: list[str] = []
    for r in results:
        lines.append(f"[source:{r.get('url', 'unknown')}]\n{r.get('content', '')}")
    return "\n\n".join(lines)
