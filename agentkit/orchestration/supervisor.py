from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from agentkit.orchestration.agent_base import BaseAgent
from agentkit.orchestration.state import AgentState

SUPERVISOR_PROMPT = """You are a workflow supervisor. Given the current task and conversation,
decide which specialist to call next or whether the task is complete.

Available specialists: {specialists}

Reply with ONLY the specialist name, or 'FINISH' if the task is complete.
Do not explain your choice."""


class SupervisorAgent(BaseAgent):
    """Routes work to specialist agents based on task state."""

    name = "supervisor"

    def __init__(
        self,
        llm: BaseChatModel,
        specialists: dict[str, BaseAgent],
        max_retries: int = 2,
    ) -> None:
        super().__init__(llm)
        self.specialists = specialists
        self.max_retries = max_retries

    def _decide_next(self, state: AgentState) -> str:
        specialist_names = ", ".join(self.specialists.keys())
        prompt = SUPERVISOR_PROMPT.format(specialists=specialist_names)
        messages = [SystemMessage(content=prompt)] + state["messages"]
        response = self.llm.invoke(messages)
        return response.content.strip()

    def run(self, state: AgentState) -> AgentState:
        next_agent = state.get("current_agent") or self._decide_next(state)

        if next_agent == "FINISH" or next_agent not in self.specialists:
            return {**state, "current_agent": "FINISH"}

        specialist = self.specialists[next_agent]
        updated = specialist.invoke(state)

        if updated.get("error") and state["retry_count"] < self.max_retries:
            return {**updated, "retry_count": state["retry_count"] + 1}

        return updated
