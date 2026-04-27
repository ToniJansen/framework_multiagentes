from __future__ import annotations

import re

MAX_OUTPUT_CHARS = 16_000
MAX_DIFF_LINES = 500

_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}", re.IGNORECASE),       # OpenAI key
    re.compile(r"sk-ant-[A-Za-z0-9\-]{20,}", re.IGNORECASE),  # Anthropic key
    re.compile(r"ghp_[A-Za-z0-9]{36}", re.IGNORECASE),        # GitHub PAT
    re.compile(r"AKIA[0-9A-Z]{16}", re.IGNORECASE),            # AWS access key
]


class OutputValidationError(Exception):
    pass


class OutputValidator:
    """Validates agent outputs. Raises OutputValidationError on violations."""

    @staticmethod
    def check_length(output: str) -> str:
        if len(output) > MAX_OUTPUT_CHARS:
            raise OutputValidationError(
                f"Output too long: {len(output)} chars (max {MAX_OUTPUT_CHARS})"
            )
        return output

    @staticmethod
    def check_no_secrets(output: str) -> str:
        for pattern in _SECRET_PATTERNS:
            if pattern.search(output):
                raise OutputValidationError(
                    "Output contains what appears to be a secret/API key. Blocked."
                )
        return output

    @staticmethod
    def check_diff_size(diff: str) -> str:
        lines = diff.splitlines()
        if len(lines) > MAX_DIFF_LINES:
            raise OutputValidationError(
                f"Diff too large: {len(lines)} lines (max {MAX_DIFF_LINES}). "
                "Break the change into smaller pieces."
            )
        return diff

    @staticmethod
    def check_has_citation(output: str) -> str:
        """Require that output includes at least one citation marker."""
        citation_markers = ["[SQL:", "[chunk:", "[source:", "[ref:"]
        if not any(marker in output for marker in citation_markers):
            raise OutputValidationError(
                "Output must cite its sources. Use [SQL: ...], [chunk: ...], or [source: ...]."
            )
        return output

    @classmethod
    def validate_agent_response(cls, output: str, require_citation: bool = False) -> str:
        cls.check_length(output)
        cls.check_no_secrets(output)
        if require_citation:
            cls.check_has_citation(output)
        return output

    @classmethod
    def validate_diff(cls, diff: str) -> str:
        cls.check_diff_size(diff)
        cls.check_no_secrets(diff)
        return diff
