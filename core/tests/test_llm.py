import pytest
from types import SimpleNamespace

from core.llm import LLMUnavailableError, _tool_input, structured_tool, anthropic_client
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
