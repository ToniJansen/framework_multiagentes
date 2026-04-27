from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def wrap_tool_call(max_retries: int = 0, redact_errors: bool = False) -> Callable[[F], F]:
    """
    Decorator factory for LangChain tools.

    Args:
        max_retries: Number of additional attempts on exception (0 = no retry).
        redact_errors: If True, replace exception detail with generic message (for prod).
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempts = max_retries + 1
            last_error: Exception | None = None
            for attempt in range(1, attempts + 1):
                try:
                    t0 = time.perf_counter()
                    result = func(*args, **kwargs)
                    elapsed = time.perf_counter() - t0
                    logger.debug(
                        "tool_call_ok",
                        extra={
                            "tool": func.__name__,
                            "attempt": attempt,
                            "elapsed_s": round(elapsed, 3),
                        },
                    )
                    return result
                except Exception as exc:
                    last_error = exc
                    logger.warning(
                        "tool_call_error",
                        extra={"tool": func.__name__, "attempt": attempt, "error": str(exc)},
                    )
                    if attempt < attempts:
                        time.sleep(0.5 * attempt)

            msg = "Tool execution failed." if redact_errors else f"Tool error: {last_error}"
            return msg

        return wrapper  # type: ignore[return-value]

    return decorator
