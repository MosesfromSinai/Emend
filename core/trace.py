"""JSONL call tracing for real-mode LLM usage.

Disabled unless EMEND_TRACE_PATH is set, so normal test runs and MOCK=1
production write nothing. When enabled, one line per structured call feeds
the cost-per-run numbers documented from eval runs.
"""

import json
import os
import time
from pathlib import Path


def trace_path() -> Path | None:
    raw = os.getenv("EMEND_TRACE_PATH")
    return Path(raw) if raw else None


def record_call(
    *,
    label: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_input_tokens: int = 0,
    cache_creation_input_tokens: int = 0,
) -> None:
    path = trace_path()
    if path is None:
        return
    entry = {
        "ts": time.time(),
        "label": label,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_input_tokens": cache_read_input_tokens,
        "cache_creation_input_tokens": cache_creation_input_tokens,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(entry) + "\n")
