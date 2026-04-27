from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

from agentkit.guardrails.inputs import AgentInput
from agentkit.guardrails.outputs import OutputValidator
from agentkit.observability.logging import get_logger
from agentkit.observability.tracing import get_langfuse_handler
from agentkit.orchestration.agent_base import BaseAgent
from agentkit.orchestration.state import AgentState
from agentkit.orchestration.supervisor import SupervisorAgent
from agentkit.tools.file_ops import list_files, read_file, write_file
from cases.dev_agent.prompts import CODEWRITER_PROMPT, PLANNER_PROMPT, REVIEWER_PROMPT
from cases.dev_agent.tools import validate_diff

load_dotenv()
logger = get_logger("dev_agent")

SAMPLE_REPO = Path(__file__).parent / "sample_repo"
OUT_DIR = Path(__file__).parent.parent.parent / "out"

MAX_REVIEWER_RETRIES = 2


def _llm(model: str = "gpt-4o-mini"):
    handlers = []
    lf = get_langfuse_handler()
    if lf:
        handlers.append(lf)
    return init_chat_model(
        model,
        model_provider="openai",
        callbacks=handlers if handlers else None,
    )


class PlannerAgent(BaseAgent):
    name = "planner"

    def run(self, state: AgentState) -> AgentState:
        spec = state["metadata"].get("spec", "")
        files = list_files.invoke({"directory": str(SAMPLE_REPO)})
        messages = [
            SystemMessage(content=PLANNER_PROMPT),
            HumanMessage(content=f"SPEC:\n{spec}\n\nREPO FILES:\n{files}"),
        ]
        response = self.llm.invoke(messages)
        try:
            plan = json.loads(response.content)
        except json.JSONDecodeError:
            plan = {"summary": response.content, "files_to_modify": [], "steps": []}
        return {**state, "current_agent": "codewriter", "metadata": {**state["metadata"], "plan": plan}}


class CodeWriterAgent(BaseAgent):
    name = "codewriter"

    def run(self, state: AgentState) -> AgentState:
        spec = state["metadata"].get("spec", "")
        plan = state["metadata"].get("plan", {})
        feedback = state["metadata"].get("reviewer_feedback", "")

        file_contents: dict[str, str] = {}
        for rel_path in plan.get("files_to_modify", []):
            abs_path = Path(__file__).parent.parent.parent / rel_path
            file_contents[rel_path] = read_file.invoke({"path": str(abs_path)})

        files_block = "\n\n".join(
            f"FILE: {p}\n```\n{c}\n```" for p, c in file_contents.items()
        )
        feedback_block = f"\nPREVIOUS REVIEWER FEEDBACK:\n{feedback}\n" if feedback else ""

        messages = [
            SystemMessage(content=CODEWRITER_PROMPT),
            HumanMessage(content=f"SPEC:\n{spec}\n\nPLAN:\n{json.dumps(plan, indent=2)}\n\n{files_block}{feedback_block}"),
        ]
        response = self.llm.invoke(messages)
        diff = response.content.strip()

        return {**state, "current_agent": "reviewer", "metadata": {**state["metadata"], "diff": diff}}


class ReviewerAgent(BaseAgent):
    name = "reviewer"

    def run(self, state: AgentState) -> AgentState:
        spec = state["metadata"].get("spec", "")
        diff = state["metadata"].get("diff", "")

        validation = validate_diff.invoke({"diff": diff})
        if validation != "OK":
            return {
                **state,
                "current_agent": "codewriter",
                "metadata": {**state["metadata"], "reviewer_feedback": f"Guardrail: {validation}"},
            }

        messages = [
            SystemMessage(content=REVIEWER_PROMPT),
            HumanMessage(content=f"SPEC:\n{spec}\n\nDIFF:\n{diff}"),
        ]
        response = self.llm.invoke(messages)
        verdict = response.content.strip()

        if verdict.startswith("APPROVED"):
            return {**state, "current_agent": "FINISH", "metadata": {**state["metadata"], "approved_diff": diff}}

        feedback = verdict.replace("REJECTED:", "").strip()
        retries = state["retry_count"]
        if retries >= MAX_REVIEWER_RETRIES:
            logger.warning("max_retries_reached", extra={"retries": retries})
            return {**state, "current_agent": "FINISH", "metadata": {**state["metadata"], "approved_diff": diff, "warning": "max_retries"}}

        return {
            **state,
            "current_agent": "codewriter",
            "retry_count": retries + 1,
            "metadata": {**state["metadata"], "reviewer_feedback": feedback},
        }


def run(spec_path: str) -> dict:
    spec_text = Path(spec_path).read_text(encoding="utf-8")
    AgentInput(content=spec_text)

    llm = _llm()
    specialists = {
        "planner": PlannerAgent(llm=llm),
        "codewriter": CodeWriterAgent(llm=llm),
        "reviewer": ReviewerAgent(llm=llm),
    }
    supervisor = SupervisorAgent(llm=llm, specialists=specialists, max_retries=MAX_REVIEWER_RETRIES)

    initial_state = AgentState(
        messages=[HumanMessage(content=spec_text)],
        current_agent="planner",
        retry_count=0,
        metadata={"spec": spec_text},
        error=None,
    )

    state = initial_state
    max_steps = 10
    for _ in range(max_steps):
        agent_name = state["current_agent"]
        if agent_name in ("FINISH", ""):
            break
        if agent_name not in specialists:
            break
        state = specialists[agent_name].invoke(state)

    diff = state["metadata"].get("approved_diff", state["metadata"].get("diff", ""))
    plan = state["metadata"].get("plan", {})

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    diff_path = OUT_DIR / "diff.patch"
    pr_path = OUT_DIR / "PR_description.md"

    diff_path.write_text(diff, encoding="utf-8")

    pr_description = f"""# {plan.get("summary", "Feature implementation")}

## Changes

{chr(10).join(f"- {s}" for s in plan.get("steps", []))}

## Files modified

{chr(10).join(f"- `{f}`" for f in plan.get("files_to_modify", []))}

## How to apply

```bash
git apply out/diff.patch
```

---
*Generated by dev_agent — framework_multiagentes*
"""
    pr_path.write_text(pr_description, encoding="utf-8")

    logger.info("case1_complete", extra={"diff_path": str(diff_path), "pr_path": str(pr_path)})
    return {"diff_path": str(diff_path), "pr_path": str(pr_path), "plan": plan}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="dev_agent — generate a PR draft from a spec")
    parser.add_argument("--spec", required=True, help="Path to spec markdown file")
    args = parser.parse_args()
    result = run(args.spec)
    print(f"\nDone.\n  diff: {result['diff_path']}\n  PR:   {result['pr_path']}")
