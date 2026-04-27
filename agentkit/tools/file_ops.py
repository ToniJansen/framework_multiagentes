from __future__ import annotations

from pathlib import Path

from langchain_core.tools import tool

from agentkit.guardrails.middleware import wrap_tool_call
from agentkit.guardrails.policies import PolicyGate
import agentkit.guardrails.policies as _pol

WORKSPACE_ROOT = Path(__file__).parent.parent.parent


@tool
@wrap_tool_call()
def read_file(path: str) -> str:
    """Read a file from the workspace. Returns its text content."""
    safe = PolicyGate.check_file_read(path, allowed_roots=[_pol.WORKSPACE_ROOT])
    return safe.read_text(encoding="utf-8")


@tool
@wrap_tool_call()
def write_file(path: str, content: str) -> str:
    """Write content to a file inside the out/ directory."""
    safe = PolicyGate.check_file_write(path)
    safe.parent.mkdir(parents=True, exist_ok=True)
    safe.write_text(content, encoding="utf-8")
    return f"Written: {safe}"


@tool
@wrap_tool_call()
def list_files(directory: str) -> str:
    """List files in a workspace directory (non-recursive)."""
    safe = PolicyGate.check_file_read(directory, allowed_roots=[_pol.WORKSPACE_ROOT])
    if not safe.is_dir():
        return f"Not a directory: {safe}"
    files = sorted(str(p.relative_to(_pol.WORKSPACE_ROOT)) for p in safe.iterdir())
    return "\n".join(files) if files else "(empty)"
