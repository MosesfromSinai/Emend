import pytest

from core.llm import LLMUnavailableError, structured_tool, anthropic_client
from core.schemas import JDExtract


def test_anthropic_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(LLMUnavailableError, match="ANTHROPIC_API_KEY"):
        anthropic_client()


def test_structured_tool_uses_schema_contract():
    tool = structured_tool(JDExtract)

    assert tool["name"] == "emit_schema"
    assert tool["input_schema"]["required"] == list(JDExtract.model_fields)
