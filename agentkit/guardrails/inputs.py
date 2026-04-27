from __future__ import annotations

import re
from functools import wraps
from typing import Any, Callable

from pydantic import BaseModel, field_validator

MAX_INPUT_CHARS = 8_000
INJECTION_PATTERNS = [
    r"ignore (previous|all) instructions",
    r"system prompt",
    r"jailbreak",
    r"you are now",
    r"pretend (you are|to be)",
]


class AgentInput(BaseModel):
    content: str
    source: str = "user"

    @field_validator("content")
    @classmethod
    def check_length(cls, v: str) -> str:
        if len(v) > MAX_INPUT_CHARS:
            raise ValueError(f"Input exceeds {MAX_INPUT_CHARS} characters ({len(v)})")
        return v

    @field_validator("content")
    @classmethod
    def check_injection(cls, v: str) -> str:
        lower = v.lower()
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, lower):
                raise ValueError(f"Potential prompt injection detected: '{pattern}'")
        return v


def validate_input(func: Callable) -> Callable:
    """Decorator that validates the first string argument as AgentInput."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        new_args = list(args)
        for i, arg in enumerate(new_args):
            if isinstance(arg, str):
                AgentInput(content=arg)  # raises ValueError on violation
                break
        return func(*new_args, **kwargs)

    return wrapper
