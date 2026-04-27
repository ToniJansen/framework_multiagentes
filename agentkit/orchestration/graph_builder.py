from __future__ import annotations

from langgraph.graph import END, StateGraph

from agentkit.orchestration.state import AgentState
from agentkit.orchestration.supervisor import SupervisorAgent


def build_graph(supervisor: SupervisorAgent) -> StateGraph:
    """Build a LangGraph StateGraph from a supervisor and its registered specialists.

    The graph has one node per specialist plus a supervisor node.
    Routing: supervisor -> specialist -> supervisor -> ... -> END.
    """
    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor.run)

    for name, agent in supervisor.specialists.items():
        graph.add_node(name, agent.run)

    graph.set_entry_point("supervisor")

    def route(state: AgentState) -> str:
        next_agent = state.get("current_agent", "")
        if next_agent == "FINISH" or not next_agent:
            return END
        return next_agent if next_agent in supervisor.specialists else END

    graph.add_conditional_edges("supervisor", route)

    for name in supervisor.specialists:
        graph.add_edge(name, "supervisor")

    return graph
