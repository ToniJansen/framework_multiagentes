from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from agentkit.orchestration.state import AgentState


class BaseAgent(ABC):
    """Base for all specialist agents in the platform."""

    name: str = "base"

    def __init__(self, llm: BaseChatModel, tools: list[BaseTool] | None = None) -> None:
        self.llm = llm
        self.tools = tools or []

    @abstractmethod
    def run(self, state: AgentState) -> AgentState:
        """Process the current state and return an updated state."""

    def invoke(self, state: AgentState) -> AgentState:
        from agentkit.observability.tracing import trace_agent

        with trace_agent(self.name, state):
            return self.run(state)
