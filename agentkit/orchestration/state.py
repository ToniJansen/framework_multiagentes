from __future__ import annotations

from typing import Annotated, Any

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    current_agent: str
    retry_count: int
    metadata: dict[str, Any]
    error: str | None
