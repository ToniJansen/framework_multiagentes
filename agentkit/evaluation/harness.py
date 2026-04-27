from __future__ import annotations

import json
import sys
from pathlib import Path

from agentkit.evaluation.criteria import check_diff_quality, check_response_quality
from agentkit.observability.logging import get_logger

logger = get_logger("eval_harness")

GOLDENS_DIR = Path(__file__).parent / "goldens"


def run_spec_to_pr_eval() -> list[dict]:
    from cases.spec_to_pr.main import run as run_spec_to_pr

    goldens = json.loads((GOLDENS_DIR / "spec_to_pr.json").read_text())
    results = []

    for golden in goldens:
        logger.info("eval_start", extra={"golden_id": golden["id"]})
        try:
            output = run_spec_to_pr(golden["input_spec"])
            diff = Path(output["diff_path"]).read_text()
            pr = Path(output["pr_path"]).read_text()

            diff_result = check_diff_quality(diff, golden["expected"])
            pr_keywords = golden["expected"].get("pr_description_contains", [])
            pr_ok = all(kw.lower() in pr.lower() for kw in pr_keywords)

            results.append({
                "id": golden["id"],
                "passed": diff_result.passed and pr_ok,
                "diff_score": diff_result.score,
                "diff_reason": diff_result.reason,
                "pr_ok": pr_ok,
            })
        except Exception as exc:
            results.append({"id": golden["id"], "passed": False, "error": str(exc)})

    return results


def print_report(results: list[dict]) -> bool:
    passed = sum(1 for r in results if r.get("passed"))
    total = len(results)
    print(f"\nEvaluation: {passed}/{total} passed\n")
    for r in results:
        status = "PASS" if r.get("passed") else "FAIL"
        print(f"  [{status}] {r['id']}")
        if not r.get("passed"):
            print(f"         reason: {r.get('diff_reason') or r.get('error')}")
    return passed == total


if __name__ == "__main__":
    results = run_spec_to_pr_eval()
    all_passed = print_report(results)
    sys.exit(0 if all_passed else 1)
