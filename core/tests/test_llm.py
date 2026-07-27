import pytest

from core.llm import LLMUnavailableError, anthropic_client


def test_anthropic_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(LLMUnavailableError, match="ANTHROPIC_API_KEY"):
        anthropic_client()
