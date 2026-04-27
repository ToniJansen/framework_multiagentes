from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import HumanMessage

from agentkit.orchestration.agent_base import BaseAgent
from agentkit.orchestration.graph_builder import build_graph
from agentkit.orchestration.state import AgentState
from agentkit.orchestration.supervisor import SupervisorAgent


def make_state(msg: str = "hello", agent: str = "", retries: int = 0) -> AgentState:
    return AgentState(
        messages=[HumanMessage(content=msg)],
        current_agent=agent,
        retry_count=retries,
        metadata={},
        error=None,
    )


class EchoAgent(BaseAgent):
    name = "echo"

    def run(self, state: AgentState) -> AgentState:
        return {**state, "current_agent": "FINISH", "metadata": {"echoed": True}}


class ErrorAgent(BaseAgent):
    name = "errorer"

    def run(self, state: AgentState) -> AgentState:
        return {**state, "error": "something went wrong"}


class TestAgentState:
    def test_state_creation(self):
        s = make_state("test")
        assert s["messages"][0].content == "test"
        assert s["retry_count"] == 0
        assert s["error"] is None


class TestSupervisor:
    def _make_supervisor(self, specialists):
        llm = MagicMock()
        llm.invoke.return_value = MagicMock(content="echo")
        return SupervisorAgent(llm=llm, specialists=specialists)

    def test_routes_to_specialist(self):
        echo = EchoAgent(llm=MagicMock())
        sup = self._make_supervisor({"echo": echo})
        state = make_state(agent="echo")
        result = sup.run(state)
        assert result["metadata"].get("echoed") is True

    def test_finish_on_unknown_agent(self):
        sup = self._make_supervisor({})
        state = make_state(agent="nonexistent")
        result = sup.run(state)
        assert result["current_agent"] == "FINISH"

    def test_retry_on_error(self):
        err = ErrorAgent(llm=MagicMock())
        sup = self._make_supervisor({"errorer": err})
        state = make_state(agent="errorer", retries=0)
        result = sup.run(state)
        assert result["retry_count"] == 1

    def test_no_retry_when_max_reached(self):
        err = ErrorAgent(llm=MagicMock())
        sup = self._make_supervisor({"errorer": err})
        state = make_state(agent="errorer", retries=2)
        result = sup.run(state)
        assert result["retry_count"] == 2


class TestGraphBuilder:
    def test_graph_compiles(self):
        llm = MagicMock()
        llm.invoke.return_value = MagicMock(content="FINISH")
        echo = EchoAgent(llm=MagicMock())
        sup = SupervisorAgent(llm=llm, specialists={"echo": echo})
        graph = build_graph(sup)
        compiled = graph.compile()
        assert compiled is not None
