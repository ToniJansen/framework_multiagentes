# 0003 — LangFuse for observability (self-hosted)

**Status:** Accepted
**Date:** 2026-04-27

## Context

Running AI agents in production requires visibility into: which agent ran, what prompt it received, what the LLM responded, how many tokens were used, what it cost, and how long it took. Without this, debugging and cost management are guesswork.

Several observability options exist for LLM (Large Language Model) pipelines: LangFuse, LangSmith (Smith LM), Helicone, Weights & Biases (W&B) Prompts, and custom logging.

## Decision

Use **LangFuse** (Language Fuse) self-hosted via Docker as the observability backend.

Integration: `agentkit/observability/tracing.py` provides `trace_agent()` (context manager) and `get_langfuse_handler()` (LangChain callback). Both fail-safe — if `LANGFUSE_SECRET_KEY` is not set, they no-op cleanly, allowing the platform to run without observability configured.

## Alternatives considered

| Alternative | Reason not chosen |
|-------------|-------------------|
| LangSmith | Requires paid tier for teams, US-hosted SaaS only. Not self-hostable. Vendor lock-in. |
| Helicone | SaaS-only. Data leaves the environment. |
| W&B Prompts | Good for ML experiments, but heavier than needed for agent traces. |
| Custom JSON logging only | `agentkit/observability/logging.py` provides structured logging, but lacks the trace/span UI and cost dashboard that LangFuse offers. |

## Consequences

**Positive:**
- Full trace tree per agent invocation: which tools were called, in what order, with what inputs/outputs.
- Token and cost tracking per span (usable with `TokenCounterCallback`).
- Self-hosted: data stays local. No SaaS subscription for a local/demo environment.
- MIT License — no vendor lock-in.

**Negative / trade-offs:**
- LangFuse server runs as a Docker container (adds ~300 MB to compose stack).
- LangFuse 2.x -> 3.x migration may require config changes.

**Risks:**
- Self-hosted deployment requires maintaining the LangFuse Docker image version. Pin it and test upgrades in isolation.
