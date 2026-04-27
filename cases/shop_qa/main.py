from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

from agentkit.guardrails.inputs import AgentInput
from agentkit.guardrails.outputs import OutputValidator, OutputValidationError
from agentkit.observability.logging import get_logger
from agentkit.observability.tracing import get_langfuse_handler
from agentkit.orchestration.agent_base import BaseAgent
from agentkit.orchestration.state import AgentState
from agentkit.tools.sql_safe import run_sql
from agentkit.tools.vector_search import vector_search
from cases.shop_qa.prompts import ANALYST_PROMPT, REPORTER_PROMPT, RESEARCHER_PROMPT

load_dotenv()
logger = get_logger("shop_qa")

MAX_RETRIES = 1


def _llm(model: str = "gpt-4o-mini"):
    handlers = []
    lf = get_langfuse_handler()
    if lf:
        handlers.append(lf)
    return init_chat_model(model, model_provider="openai", callbacks=handlers or None)


class AnalystAgent(BaseAgent):
    name = "analyst"

    def run(self, state: AgentState) -> AgentState:
        question = state["metadata"].get("question", "")
        messages = [SystemMessage(content=ANALYST_PROMPT), HumanMessage(content=question)]
        response = self.llm.invoke(messages)
        sql_query = response.content.strip()
        sql_result = run_sql.invoke({"query": sql_query})
        return {
            **state,
            "current_agent": "researcher",
            "metadata": {**state["metadata"], "sql_query": sql_query, "sql_result": sql_result},
        }


class ResearcherAgent(BaseAgent):
    name = "researcher"

    def run(self, state: AgentState) -> AgentState:
        question = state["metadata"].get("question", "")
        messages = [SystemMessage(content=RESEARCHER_PROMPT), HumanMessage(content=question)]
        self.llm.invoke(messages)
        chunks = vector_search.invoke({"query": question, "top_k": 3})
        return {
            **state,
            "current_agent": "reporter",
            "metadata": {**state["metadata"], "chunks": chunks},
        }


class ReporterAgent(BaseAgent):
    name = "reporter"

    def run(self, state: AgentState) -> AgentState:
        question = state["metadata"].get("question", "")
        sql_result = state["metadata"].get("sql_result", "")
        sql_query = state["metadata"].get("sql_query", "")
        chunks = state["metadata"].get("chunks", "")
        retry = state["metadata"].get("reporter_retry", 0)

        context = (
            f"QUESTION: {question}\n\n"
            f"SQL DATA [SQL: {sql_query}]:\n{sql_result}\n\n"
            f"REVIEW EXCERPTS:\n{chunks}"
        )
        messages = [SystemMessage(content=REPORTER_PROMPT), HumanMessage(content=context)]
        response = self.llm.invoke(messages)
        answer = response.content.strip()

        try:
            OutputValidator.validate_agent_response(answer, require_citation=True)
            return {
                **state,
                "current_agent": "FINISH",
                "metadata": {**state["metadata"], "answer": answer},
            }
        except OutputValidationError:
            if retry >= MAX_RETRIES:
                return {
                    **state,
                    "current_agent": "FINISH",
                    "metadata": {**state["metadata"], "answer": answer, "warning": "citation_missing"},
                }
            return {
                **state,
                "current_agent": "reporter",
                "metadata": {**state["metadata"], "reporter_retry": retry + 1},
            }


def run(question: str) -> str:
    AgentInput(content=question)
    llm = _llm()
    specialists = {
        "analyst": AnalystAgent(llm=llm),
        "researcher": ResearcherAgent(llm=llm),
        "reporter": ReporterAgent(llm=llm),
    }

    state = AgentState(
        messages=[HumanMessage(content=question)],
        current_agent="analyst",
        retry_count=0,
        metadata={"question": question},
        error=None,
    )

    max_steps = 10
    for _ in range(max_steps):
        agent_name = state["current_agent"]
        if agent_name in ("FINISH", ""):
            break
        if agent_name not in specialists:
            break
        state = specialists[agent_name].invoke(state)

    return state["metadata"].get("answer", "(no answer generated)")


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "Qual a média de avaliação dos produtos?"
    print(run(question))
