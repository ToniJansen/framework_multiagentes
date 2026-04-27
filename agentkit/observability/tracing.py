from __future__ import annotations

import os
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generator

if TYPE_CHECKING:
    from agentkit.orchestration.state import AgentState


@contextmanager
def trace_agent(
    agent_name: str,
    state: "AgentState",
    **extra: Any,
) -> Generator[None, None, None]:
    """Wrap an agent invocation in a LangFuse trace span.

    No-ops cleanly if LANGFUSE_SECRET_KEY is not set.
    """
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    if not secret_key:
        yield
        return

    try:
        from langfuse import Langfuse

        lf = Langfuse(
            secret_key=secret_key,
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
            host=os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
        )
        trace = lf.trace(name=agent_name, metadata={**extra})
        span = trace.span(name=f"{agent_name}_run")
        try:
            yield
        finally:
            span.end()
            lf.flush()
    except Exception:
        yield


def get_langfuse_handler():
    """Return a LangFuse CallbackHandler for LangChain, or None if not configured."""
    if not os.getenv("LANGFUSE_SECRET_KEY"):
        return None
    try:
        from langfuse.callback import CallbackHandler

        return CallbackHandler(
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
            host=os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
        )
    except Exception:
        return None
