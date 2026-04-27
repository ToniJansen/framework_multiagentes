# 0005 — LLM provider abstraction with OpenAI as default

**Status:** Accepted
**Date:** 2026-04-27

## Context

The platform must not be coupled to a single LLM (Large Language Model) provider. Providers change pricing, deprecate models, and have different strengths. The ability to swap providers without rewriting agent code is a platform requirement.

## Decision

Use **`init_chat_model`** from `langchain.chat_models` as the single entry point for LLM instantiation. Default model: `gpt-4o-mini` (OpenAI) — lowest cost for demonstration. Swapping to Anthropic Claude Sonnet requires only changing the `model` and `model_provider` parameters, with no changes to agent logic.

```python
llm = init_chat_model("gpt-4o-mini", model_provider="openai")
# Or:
llm = init_chat_model("claude-sonnet-4-6", model_provider="anthropic")
```

Both are supported via `langchain-openai` and `langchain-anthropic` packages already in `pyproject.toml`.

## Alternatives considered

| Alternative | Reason not chosen |
|-------------|-------------------|
| Direct `ChatOpenAI()` instantiation | Tightly couples agent code to OpenAI. Swapping providers requires editing every agent file. |
| LiteLLM proxy | Adds a network proxy service. Useful for multi-org deployments but overengineered for a single-platform portfolio project. |
| Bedrock (AWS) | Valid for enterprise, but adds AWS credential complexity to a local-first demo. Supported by the abstraction — add later if needed. |

## Consequences

**Positive:**
- Provider swap is a one-line change in `main.py` of each case.
- LangFuse tracing works identically regardless of provider (uses LangChain callbacks).
- New providers (Gemini, Mistral) can be added without touching agent code.

**Negative / trade-offs:**
- `init_chat_model` requires the corresponding LangChain provider package to be installed.
- Model capability differences (context window, JSON mode, tool calling) must be verified per provider.

**Risks:**
- `init_chat_model` API may change across LangChain minor versions. Pin `langchain>=0.3.0` and test on upgrade.
