"""Small Anthropic client helpers for real pipeline mode."""

import os
from typing import Any

from pydantic import BaseModel

STRUCTURED_TOOL_NAME = "emit_schema"
DEFAULT_MAX_TOKENS = 4096


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


def structured_call[SchemaT: BaseModel](
    model: str,
    system: str,
    user: str,
    schema: type[SchemaT],
    *,
    client: Any | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> SchemaT:
    """Force Claude to return a Pydantic-validated object."""
    llm = client or anthropic_client()
    response = llm.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
        tools=[structured_tool(schema)],
        tool_choice={"type": "tool", "name": STRUCTURED_TOOL_NAME},
    )
    return schema.model_validate(_tool_input(response))
