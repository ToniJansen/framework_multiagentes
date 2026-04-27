from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DiffQualityResult:
    passed: bool
    reason: str
    score: float


def check_diff_quality(diff: str, expected: dict) -> DiffQualityResult:
    """Check a diff against expected criteria without LLM involvement."""
    if not diff or diff.strip() == "(no changes)":
        return DiffQualityResult(passed=False, reason="Empty diff", score=0.0)

    if expected.get("diff_starts_with") and not diff.lstrip().startswith(expected["diff_starts_with"]):
        return DiffQualityResult(
            passed=False,
            reason=f"Diff must start with '{expected['diff_starts_with']}'",
            score=0.1,
        )

    missing = [
        kw for kw in expected.get("diff_contains", [])
        if kw.lower() not in diff.lower()
    ]
    if missing:
        return DiffQualityResult(
            passed=False,
            reason=f"Diff missing expected content: {missing}",
            score=0.5,
        )

    return DiffQualityResult(passed=True, reason="All criteria met", score=1.0)


def check_response_quality(response: str, expected: dict) -> DiffQualityResult:
    """Check a chat response against expected criteria."""
    if expected.get("response_not_empty") and not response.strip():
        return DiffQualityResult(passed=False, reason="Empty response", score=0.0)

    citation_markers = ["[SQL:", "[chunk:", "[source:", "[ref:"]
    if expected.get("response_contains_citation"):
        if not any(m in response for m in citation_markers):
            return DiffQualityResult(
                passed=False,
                reason="Response missing citation marker",
                score=0.5,
            )

    return DiffQualityResult(passed=True, reason="All criteria met", score=1.0)
