import pytest
from types import SimpleNamespace

from core.llm import LLMUnavailableError, _tool_input, structured_call, structured_tool, anthropic_client
from core.schemas import JDExtract


def test_anthropic_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(LLMUnavailableError, match="ANTHROPIC_API_KEY"):
        anthropic_client()


def test_structured_tool_uses_schema_contract():
    tool = structured_tool(JDExtract)

    assert tool["name"] == "emit_schema"
    assert tool["input_schema"]["required"] == list(JDExtract.model_fields)


def test_tool_input_extracts_structured_payload():
    response = SimpleNamespace(
        content=[SimpleNamespace(type="tool_use", name="emit_schema", input={"ok": True})]
    )

    assert _tool_input(response) == {"ok": True}


def test_tool_input_rejects_missing_structured_payload():
    response = SimpleNamespace(content=[SimpleNamespace(type="text", text="not structured")])

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
