from types import SimpleNamespace

import pytest

from core.llm import (
    DEFAULT_TIMEOUT_SECONDS,
    LLMUnavailableError,
    _tool_input,
    anthropic_client,
    structured_call,
    structured_tool,
)
from core.schemas import JDExtract


def test_anthropic_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(LLMUnavailableError, match="ANTHROPIC_API_KEY"):
        anthropic_client()


def test_anthropic_client_reuses_instance_for_same_key():
    assert anthropic_client("test-key-a") is anthropic_client("test-key-a")


def test_anthropic_client_builds_separately_per_key():
    assert anthropic_client("test-key-b") is not anthropic_client("test-key-c")


def test_anthropic_client_has_an_explicit_timeout():
    # a background job stuck on one indefinitely-hanging call is a job
    # stuck in "running" forever -- this must never be left to whatever the
    # SDK's own unstated default happens to be
    client = anthropic_client("test-key-timeout")
    assert client.timeout == DEFAULT_TIMEOUT_SECONDS


def test_structured_tool_uses_schema_contract():
    tool = structured_tool(JDExtract)
    required = [name for name, field in JDExtract.model_fields.items() if field.is_required()]

    assert tool["name"] == "emit_schema"
    assert tool["input_schema"]["required"] == required


def test_tool_input_extracts_structured_payload():
    response = SimpleNamespace(
        content=[
            SimpleNamespace(type="tool_use", name="emit_schema", input={"ok": True})
        ]
    )

    assert _tool_input(response) == {"ok": True}


def test_tool_input_rejects_missing_structured_payload():
    response = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="not structured")]
    )

    with pytest.raises(LLMUnavailableError, match="structured tool output"):
        _tool_input(response)


def test_structured_call_forces_tool_and_validates_schema():
    payload = {
        "company": "Acme",
        "title": "Engineer",
        "hard_skills": ["Python"],
        "soft_requirements": [],
        "responsibilities": [],
        "keywords": ["Python"],
    }
    block = SimpleNamespace(type="tool_use", name="emit_schema", input=payload)
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(content=[block])

    messages = SimpleNamespace(create=create)
    client = SimpleNamespace(messages=messages)

    result = structured_call("model", "system", "user", JDExtract, client=client)

    assert result == JDExtract(**payload)
    assert calls[0]["tool_choice"] == {"type": "tool", "name": "emit_schema"}


def test_structured_call_logs_before_reraising_an_api_failure(caplog):
    # Reached only once the SDK's own internal retry/backoff is fully
    # exhausted -- previously a bare stack trace with no indication of
    # which model/schema was mid-call when it gave up.
    def create(**kwargs):
        raise ConnectionError("connection reset")

    client = SimpleNamespace(messages=SimpleNamespace(create=create))

    with caplog.at_level("ERROR", logger="emend.core.llm"):
        with pytest.raises(ConnectionError):
            structured_call("model", "system", "user", JDExtract, client=client)

    assert "model" in caplog.text
    assert "JDExtract" in caplog.text
