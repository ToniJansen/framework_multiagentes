from __future__ import annotations

import json
import logging
import sys
import time
from contextlib import contextmanager
from typing import Any, Generator


class JsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        extra = {
            k: v
            for k, v in record.__dict__.items()
            if k not in logging.LogRecord.__dict__ and not k.startswith("_")
        }
        payload.update(extra)
        return json.dumps(payload, ensure_ascii=False, default=str)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


@contextmanager
def log_span(
    logger: logging.Logger,
    span_name: str,
    **extra: Any,
) -> Generator[dict[str, Any], None, None]:
    """Context manager that logs start/end of a named span with duration."""
    ctx: dict[str, Any] = {"span": span_name, **extra}
    t0 = time.perf_counter()
    logger.info("span_start", extra=ctx)
    try:
        yield ctx
    except Exception as exc:
        ctx["error"] = str(exc)
        logger.error("span_error", extra=ctx)
        raise
    finally:
        ctx["elapsed_ms"] = round((time.perf_counter() - t0) * 1000)
        logger.info("span_end", extra=ctx)
