from __future__ import annotations

import difflib

from langchain_core.tools import tool

from agentkit.guardrails.middleware import wrap_tool_call
from agentkit.guardrails.outputs import OutputValidator


@tool
@wrap_tool_call()
def generate_diff(original: str, modified: str, filename: str) -> str:
    """Generate a unified diff between original and modified file content.

    Args:
        original: original file content
        modified: modified file content
        filename: relative file path (used in diff header)
    """
    diff_lines = list(difflib.unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm="",
    ))
    return "".join(diff_lines) if diff_lines else "(no changes)"


@tool
@wrap_tool_call()
def validate_diff(diff: str) -> str:
    """Validate a unified diff for size and secrets. Returns 'OK' or an error message."""
    try:
        OutputValidator.validate_diff(diff)
        if not diff.startswith("---"):
            return "Invalid diff: must start with '---'"
        return "OK"
    except Exception as exc:
        return f"Validation failed: {exc}"
