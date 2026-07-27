"""Small Anthropic client helpers for real pipeline mode."""

import os
from typing import Any

from pydantic import BaseModel

STRUCTURED_TOOL_NAME = "emit_schema"


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


def structured_tool(schema: type[BaseModel]) -> dict[str, Any]:
    """Build the forced tool schema used by structured LLM calls."""
    return {
        "name": STRUCTURED_TOOL_NAME,
        "description": f"Return a valid {schema.__name__} object.",
        "input_schema": schema.model_json_schema(),
    }


def _tool_input(response: Any) -> dict[str, Any]:
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == STRUCTURED_TOOL_NAME:
            return block.input
    raise LLMUnavailableError("Anthropic response did not include structured tool output")
