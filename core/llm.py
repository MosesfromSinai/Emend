"""Small Anthropic client helpers for real pipeline mode."""

import copy
import logging
import os
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

logger = logging.getLogger("emend.core.llm")

STRUCTURED_TOOL_NAME = "emit_schema"
DEFAULT_MAX_TOKENS = 16000
# Explicit rather than relying on the SDK's own (unstated-here) default --
# a background job stuck on one indefinitely-hanging call is a job stuck in
# "running" forever, and every route that touches this is already a
# multi-minute background task, not a request a browser is blocked on.
DEFAULT_TIMEOUT_SECONDS = 120.0

# Per 00-project-brief.md: Sonnet tailors, Haiku structures/extracts/judges.
TAILOR_MODEL = "claude-sonnet-5"
FAST_MODEL = "claude-haiku-4-5"


class LLMUnavailableError(RuntimeError):
    """Raised when real LLM mode is requested but not configured."""


@dataclass
class StructuredResult[SchemaT: BaseModel]:
    """A validated object plus the token usage that produced it."""

    value: SchemaT
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


_client_cache: dict[str, Any] = {}


def anthropic_client(api_key: str | None = None) -> Any:
    """Return a cached client for this key, building one on first use.

    Real mode makes many calls per application (a tailor call plus one judge
    call per bullet); reusing one client reuses its connection pool instead
    of opening a fresh one per call. Keyed by the resolved key, not cached
    globally, so a missing key still raises every time instead of serving a
    stale client from an earlier, differently-configured call.
    """
    key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise LLMUnavailableError("ANTHROPIC_API_KEY is required when MOCK=0")
    if key not in _client_cache:
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise LLMUnavailableError("anthropic package is required when MOCK=0") from exc
        _client_cache[key] = Anthropic(api_key=key, timeout=DEFAULT_TIMEOUT_SECONDS)
    return _client_cache[key]


def _forbid_extra_properties(node: Any) -> None:
    """Recursively require additionalProperties=false, as strict tools demand."""
    if isinstance(node, dict):
        if node.get("type") == "object" and "additionalProperties" not in node:
            node["additionalProperties"] = False
        for value in node.values():
            _forbid_extra_properties(value)
    elif isinstance(node, list):
        for item in node:
            _forbid_extra_properties(item)


def supports_strict_tool(schema: type[BaseModel]) -> bool:
    """Report whether a schema can use strict tool use.

    Strict mode rejects `additionalProperties` set to anything but false, so
    open-ended maps disqualify a schema. `MasterResume` and `TailoredResume`
    both carry `skills: dict[str, list[str]]` and therefore cannot be strict;
    `JDExtract` and `BulletVerdict` can.
    """
    def has_open_map(node: Any) -> bool:
        if isinstance(node, dict):
            extra = node.get("additionalProperties")
            if isinstance(extra, dict) or extra is True:
                return True
            return any(has_open_map(value) for value in node.values())
        if isinstance(node, list):
            return any(has_open_map(item) for item in node)
        return False

    return not has_open_map(schema.model_json_schema())


def structured_tool(schema: type[BaseModel], *, strict: bool = False) -> dict[str, Any]:
    """Build the forced tool schema used by structured LLM calls."""
    input_schema = copy.deepcopy(schema.model_json_schema())
    tool: dict[str, Any] = {
        "name": STRUCTURED_TOOL_NAME,
        "description": f"Return a valid {schema.__name__} object.",
        "input_schema": input_schema,
    }
    if strict:
        _forbid_extra_properties(input_schema)
        tool["strict"] = True
    return tool


def cacheable_system(*blocks: str) -> list[dict[str, Any]]:
    """Render system text as blocks with a cache breakpoint on the last one.

    Caching is a prefix match over `tools` -> `system` -> `messages`, so the
    breakpoint on the trailing block also covers the tool schema. Prefixes
    below the model's minimum (4096 tokens on Haiku, 1024 on Sonnet) silently
    do not cache -- check `cache_creation_input_tokens` rather than assuming.
    """
    texts = [block for block in blocks if block and block.strip()]
    if not texts:
        return []
    system = [{"type": "text", "text": text} for text in texts]
    system[-1]["cache_control"] = {"type": "ephemeral"}
    return system


def _tool_input(response: Any) -> dict[str, Any]:
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == STRUCTURED_TOOL_NAME:
            return block.input
    raise LLMUnavailableError("Anthropic response did not include structured tool output")


def _usage(response: Any) -> dict[str, int]:
    usage = getattr(response, "usage", None)
    fields = (
        "input_tokens",
        "output_tokens",
        "cache_read_input_tokens",
        "cache_creation_input_tokens",
    )
    return {field: int(getattr(usage, field, 0) or 0) for field in fields}


def structured_call_with_usage[SchemaT: BaseModel](
    model: str,
    system: str | list[dict[str, Any]],
    user: str,
    schema: type[SchemaT],
    *,
    client: Any | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    strict: bool | None = None,
    retries: int = 1,
) -> StructuredResult[SchemaT]:
    """Force Claude to return a Pydantic-validated object, reporting usage."""
    llm = client or anthropic_client()
    if strict is None:
        strict = supports_strict_tool(schema)
    tools = [structured_tool(schema, strict=strict)]
    prompt = user
    last_error: ValidationError | None = None

    for _attempt in range(retries + 1):
        try:
            response = llm.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                tools=tools,
                tool_choice={"type": "tool", "name": STRUCTURED_TOOL_NAME},
            )
        except Exception:
            # The SDK already retries a transient error (rate limit,
            # connection drop, 5xx) internally with its own backoff before
            # ever raising here -- this is only reached once that's fully
            # exhausted, which was previously invisible: a bare stack trace
            # with no indication of which model/schema was mid-call when it
            # gave up.
            logger.exception(
                "Anthropic call failed for model=%s schema=%s after SDK retries",
                model,
                schema.__name__,
            )
            raise
        try:
            value = schema.model_validate(_tool_input(response))
        except ValidationError as exc:
            last_error = exc
            prompt = (
                f"{user}\n\nYour previous response failed schema validation:\n{exc}\n"
                "Return a corrected object that satisfies every constraint."
            )
            continue
        return StructuredResult(value=value, **_usage(response))

    raise LLMUnavailableError(
        f"Anthropic returned invalid {schema.__name__} output after "
        f"{retries + 1} attempts: {last_error}"
    )


def structured_call[SchemaT: BaseModel](
    model: str,
    system: str | list[dict[str, Any]],
    user: str,
    schema: type[SchemaT],
    *,
    client: Any | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    strict: bool | None = None,
    retries: int = 1,
) -> SchemaT:
    """Force Claude to return a Pydantic-validated object."""
    return structured_call_with_usage(
        model,
        system,
        user,
        schema,
        client=client,
        max_tokens=max_tokens,
        strict=strict,
        retries=retries,
    ).value
