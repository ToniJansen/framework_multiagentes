# 0001 — LangGraph vs CrewAI for multi-agent orchestration

**Status:** Accepted
**Date:** 2026-04-27

## Context

The platform needs an orchestration layer to coordinate multiple specialist agents (Planner, CodeWriter, Reviewer, Analyst, Researcher, Reporter). Two mature open-source options were evaluated: LangGraph and CrewAI (Crew Artificial Intelligence — framework for multi-agent crews).

Key requirements:
- Fine-grained control over state transitions between agents
- Ability to implement bounded retry loops (max N retries between CodeWriter and Reviewer)
- Built-in checkpointing for resumable execution (24/7 workforce model)
- Deterministic routing — supervisor decides next agent explicitly, not via LLM every time

## Decision

Use **LangGraph** as the orchestration engine.

Agents are nodes in a `StateGraph`. The supervisor reads `current_agent` from shared `AgentState` (TypedDict) and routes via `add_conditional_edges`. Retries are bounded by `retry_count` in state. LangGraph's `SqliteSaver` (dev) and `PostgresSaver` (prod) provide checkpointing.

## Alternatives considered

| Alternative | Reason not chosen |
|-------------|-------------------|
| CrewAI | Higher-level abstraction reduces control over state transitions. Retry loops are opinionated and harder to customize. Routing is LLM-driven by default (expensive). Checkpointing requires additional configuration. |
| Plain Python + LangChain agents | No built-in state graph, routing, or checkpointing. Would require reinventing what LangGraph provides. |
| AutoGen | More research-oriented, less production-ready. State management is less explicit. |

## Consequences

**Positive:**
- Explicit state machine — every transition is code, not a prompt. Auditable and testable.
- Bounded retry loops are a first-class feature (conditional edges with counter in state).
- Checkpointing is native — `thread_id` allows resuming any interrupted workflow.
- Graphs are composable — Case 1 and Case 2 share the same graph pattern.

**Negative / trade-offs:**
- LangGraph has a steeper learning curve than CrewAI for simple linear workflows.
- Graph wiring (nodes, edges, routing functions) is more verbose than CrewAI's declarative YAML.

**Risks:**
- LangGraph API evolves rapidly (0.2.x). Pin version and monitor changelogs.
