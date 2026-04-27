from __future__ import annotations

import re
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).parent.parent.parent
ALLOWED_WRITE_DIR = WORKSPACE_ROOT / "out"

_SQL_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|REPLACE|MERGE|EXEC|EXECUTE)\b",
    re.IGNORECASE,
)
_SQL_LIMIT_RE = re.compile(r"\bLIMIT\b", re.IGNORECASE)
_MULTI_STATEMENT = re.compile(r";.+", re.DOTALL)


class PolicyViolation(Exception):
    pass


class PolicyGate:
    """Stateless policy checker. All methods raise PolicyViolation on breach."""

    @staticmethod
    def check_sql(query: str) -> str:
        """Allow only SELECT queries with a mandatory LIMIT clause."""
        query = query.strip()
        if _MULTI_STATEMENT.search(query):
            raise PolicyViolation("SQL policy: multi-statement queries are not allowed.")
        if _SQL_FORBIDDEN.search(query):
            raise PolicyViolation(f"SQL policy: only SELECT is allowed. Got: {query[:80]}")
        if not _SQL_LIMIT_RE.search(query):
            raise PolicyViolation("SQL policy: query must include a LIMIT clause.")
        return query

    @staticmethod
    def check_file_write(path: str | Path) -> Path:
        """Allow writes only inside the out/ directory."""
        resolved = Path(path).resolve()
        allowed = ALLOWED_WRITE_DIR.resolve()
        if not str(resolved).startswith(str(allowed)):
            raise PolicyViolation(
                f"File policy: writes only allowed inside {allowed}. Got: {resolved}"
            )
        return resolved

    @staticmethod
    def check_file_read(path: str | Path, allowed_roots: list[Path] | None = None) -> Path:
        """Allow reads only inside whitelisted directories."""
        resolved = Path(path).resolve()
        roots = allowed_roots or [WORKSPACE_ROOT]
        if not any(str(resolved).startswith(str(r.resolve())) for r in roots):
            raise PolicyViolation(f"File policy: read outside workspace: {resolved}")
        return resolved
