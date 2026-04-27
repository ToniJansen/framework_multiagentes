from __future__ import annotations

from langchain_core.tools import tool

from agentkit.guardrails.middleware import wrap_tool_call


@tool
@wrap_tool_call()
def github_list_files(repo: str, path: str = "", ref: str = "main") -> str:
    """List files in a public GitHub repository at the given path and ref (branch/tag).

    Args:
        repo: 'owner/repo' format, e.g. 'langchain-ai/langchain'
        path: directory path inside the repo (empty string = root)
        ref: branch or tag name
    """
    import httpx

    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    params = {"ref": ref}
    resp = httpx.get(url, params=params, timeout=10)
    resp.raise_for_status()
    items = resp.json()
    lines = [f"{item['type']:5s}  {item['name']}" for item in items]
    return "\n".join(lines) if lines else "(empty)"


@tool
@wrap_tool_call()
def github_read_file(repo: str, path: str, ref: str = "main") -> str:
    """Read the raw content of a file in a public GitHub repository.

    Args:
        repo: 'owner/repo' format
        path: file path inside the repo
        ref: branch or tag name
    """
    import httpx

    url = f"https://raw.githubusercontent.com/{repo}/{ref}/{path}"
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    return resp.text
