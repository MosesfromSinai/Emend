"""Small Anthropic client helpers for real pipeline mode."""

import os
from typing import Any


class LLMUnavailableError(RuntimeError):
    """Raised when real LLM mode is requested but not configured."""


def anthropic_client(api_key: str | None = None) -> Any:
    key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise LLMUnavailableError("ANTHROPIC_API_KEY is required when MOCK=0")
    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise LLMUnavailableError("anthropic package is required when MOCK=0") from exc
    return Anthropic(api_key=key)
