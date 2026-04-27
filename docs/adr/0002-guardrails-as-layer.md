# 0002 — Guardrails as an explicit layer, not inline prompts

**Status:** Accepted
**Date:** 2026-04-27

## Context

AI agents need to be prevented from taking harmful actions: running destructive SQL, writing outside allowed directories, leaking secrets in responses, producing outputs without source citations. The question is WHERE and HOW to enforce these constraints.

Two common approaches exist:
1. **Prompt-based**: instruct the LLM (Large Language Model) in the system prompt ("never use DELETE")
2. **Code-based**: enforce rules in a dedicated layer of Python code, independent of the LLM

## Decision

Enforce all constraints in a **dedicated `agentkit/guardrails/` module** with three sub-layers:
- `inputs.py` — Pydantic v2 validators + `@validate_input` decorator (length, injection patterns)
- `policies.py` — `PolicyGate` class: `check_sql`, `check_file_write`, `check_file_read` (runtime rules)
- `outputs.py` — `OutputValidator` class: length, secrets regex, diff size, citation enforcement

Prompt instructions may still mention rules (for LLM guidance), but the code layer is the authoritative enforcement point.

## Alternatives considered

| Alternative | Reason not chosen |
|-------------|-------------------|
| Prompt-only guardrails | Fragile — any model change, fine-tuning, or prompt variation can break enforcement. Not auditable. Cannot be unit-tested. |
| External guardrails service (e.g., Guardrails AI) | Adds a network dependency and operational complexity. The constraints needed here are simple enough for pure Python. |
| LLM-as-judge for every output | Doubles LLM cost and latency per request. Not suitable for guardrails that can be checked with regex or Pydantic. |

## Consequences

**Positive:**
- Guardrails are testable: `pytest tests/test_guardrails.py` validates all rules without LLM calls.
- Enforcement is deterministic: SQL `DELETE` is blocked by regex, not by LLM judgment.
- New rules can be added to `PolicyGate` without touching any agent code.
- Audit trail: violations raise typed exceptions (`PolicyViolation`, `OutputValidationError`) that are logged.

**Negative / trade-offs:**
- Requires maintaining a separate module. Rules must be kept in sync with agent behavior.
- Code guardrails cannot catch semantic violations (e.g., factually wrong answer). For those, use evaluation (see ADR 0004).

**Risks:**
- Regex-based secret detection produces false positives. Tune patterns carefully before prod.
