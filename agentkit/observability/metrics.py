from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler


@dataclass
class UsageAccumulator:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    calls: int = 0

    def cost_usd(self, model: str = "gpt-4o-mini") -> float:
        rates = {
            "gpt-4o-mini": (0.00015, 0.00060),
            "gpt-4o": (0.005, 0.015),
            "claude-sonnet": (0.003, 0.015),
        }
        prompt_rate, completion_rate = rates.get(model, (0.001, 0.002))
        return (
            self.prompt_tokens * prompt_rate + self.completion_tokens * completion_rate
        ) / 1000


class TokenCounterCallback(BaseCallbackHandler):
    """LangChain callback that accumulates token usage across all LLM calls."""

    def __init__(self) -> None:
        self.usage = UsageAccumulator()

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        for gen in response.generations:
            for g in gen:
                usage = getattr(g, "generation_info", {}) or {}
                self.usage.prompt_tokens += usage.get("prompt_tokens", 0)
                self.usage.completion_tokens += usage.get("completion_tokens", 0)
                self.usage.total_tokens += usage.get("total_tokens", 0)
        self.usage.calls += 1
