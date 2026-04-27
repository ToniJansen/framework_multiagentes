from __future__ import annotations

import os

import psycopg2
import psycopg2.extras
from langchain_core.tools import tool

from agentkit.guardrails.middleware import wrap_tool_call
from agentkit.guardrails.policies import PolicyGate


def _get_conn() -> psycopg2.extensions.connection:
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "agentkit"),
        user=os.getenv("POSTGRES_USER", "agentkit"),
        password=os.getenv("POSTGRES_PASSWORD", "agentkit"),
    )


@tool
@wrap_tool_call()
def run_sql(query: str) -> str:
    """Execute a read-only SQL SELECT query and return results as plain text.

    Policy: only SELECT statements with a mandatory LIMIT clause are allowed.
    """
    safe_query = PolicyGate.check_sql(query)
    with _get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(safe_query)
        rows = cur.fetchall()
        if not rows:
            return "(no rows returned)"
        headers = [desc[0] for desc in cur.description]
        lines = [" | ".join(headers)]
        lines.append("-" * len(lines[0]))
        for row in rows:
            lines.append(" | ".join(str(v) for v in row))
        return "\n".join(lines)
