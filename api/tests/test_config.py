import pytest

from api.config import _resolve_database_url


def test_resolve_database_url_uses_explicit_value(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://real:creds@db.example.com/emend")
    assert _resolve_database_url() == "postgresql+psycopg://real:creds@db.example.com/emend"


def test_resolve_database_url_falls_back_in_development(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    assert _resolve_database_url() == "postgresql+psycopg://emend:emend@localhost:5432/emend"


def test_resolve_database_url_fails_loudly_outside_development(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(RuntimeError):
        _resolve_database_url()
