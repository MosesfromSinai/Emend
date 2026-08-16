import pytest

from api.config import Settings, _resolve_database_url


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


def test_settings_rejects_samesite_none_without_secure():
    # browsers reject a SameSite=None cookie that isn't also Secure --
    # silently breaking every session with no error in this app's own logs
    with pytest.raises(RuntimeError, match="requires SESSION_COOKIE_SECURE"):
        Settings(
            database_url="sqlite:///:memory:",
            session_cookie_samesite="none",
            session_cookie_secure=False,
        )


def test_settings_allows_samesite_none_with_secure():
    Settings(
        database_url="sqlite:///:memory:",
        session_cookie_samesite="none",
        session_cookie_secure=True,
    )  # no raise


def test_settings_allows_samesite_lax_without_secure():
    Settings(
        database_url="sqlite:///:memory:",
        session_cookie_samesite="lax",
        session_cookie_secure=False,
    )  # no raise -- the local-dev default combination
