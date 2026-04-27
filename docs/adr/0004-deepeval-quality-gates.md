# 0004 — DeepEval for automated agent quality gates

**Status:** Accepted
**Date:** 2026-04-27

## Context

Agents can silently degrade: a prompt change or model update may cause the Reviewer agent to approve low-quality diffs, or the Reporter agent to hallucinate answers. Manual testing does not scale. A systematic quality gate is needed.

## Decision

Use **DeepEval** (Deep Evaluation) as the evaluation framework, with golden datasets stored in version-controlled JSON files under `agentkit/evaluation/goldens/`.

`agentkit/evaluation/harness.py` loads goldens, runs each case's `run()` function, and evaluates outputs using DeepEval metrics (faithfulness, answer relevancy, custom checks). Failures are reported with diffs. In CI (Continuous Integration), `make eval` fails the build if any golden regresses.

## Alternatives considered

| Alternative | Reason not chosen |
|-------------|-------------------|
| RAGAS | Primarily designed for RAG (Retrieval-Augmented Generation) evaluation. Less suitable for code diff quality evaluation. |
| Manual review | Not repeatable, does not scale, cannot run in CI. |
| LLM-as-judge (custom) | Expensive per-run and non-deterministic. DeepEval provides structured metrics with caching. |
| PromptFoo | Good for prompt A/B testing, but less integrated with LangChain agent workflows. |

## Consequences

**Positive:**
- Goldens are version-controlled — regressions are caught before merge.
- DeepEval integrates with LangChain natively.
- Metrics are objective and reproducible (not LLM-judged for every run by default).
- `make eval` gives a clear pass/fail signal.

**Negative / trade-offs:**
- Maintaining golden datasets requires discipline — they must be updated when behavior legitimately changes.
- DeepEval evaluation may itself invoke an LLM for some metrics (faithfulness). This adds cost per eval run.

**Risks:**
- Golden dataset can become stale if agents evolve but goldens are not updated. Requires process discipline.
