import pytest

from core.config import mock_enabled


@pytest.mark.parametrize("value", ["0", "false", "no", "off", "n", "disabled", "FALSE", "Off"])
def test_mock_enabled_recognizes_common_falsy_spellings(monkeypatch, value):
    # an operator reasonably expects any of these conventions to disable
    # mock mode -- a typo/convention mismatch here silently keeps the
    # deterministic pipeline running while real per-JD tailoring is assumed
    monkeypatch.setenv("MOCK", value)
    assert mock_enabled() is False


def test_mock_enabled_defaults_true_when_unset(monkeypatch):
    monkeypatch.delenv("MOCK", raising=False)
    assert mock_enabled() is True
