"""Environment-driven settings. Everything the platform injects comes through here."""

import os
from dataclasses import dataclass, field

from core.extract import MAX_PDF_BYTES


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _resolve_database_url() -> str:
    raw = os.environ.get("DATABASE_URL")
    if raw:
        return raw
    # The local-dev default (matching infra/docker-compose.yml's throwaway
    # `emend:emend` Postgres) is only ever used when ENVIRONMENT is left at
    # its "development" default -- outside that, a missing DATABASE_URL
    # fails loudly at startup instead of silently resolving to a
    # plausible-looking connection string with weak, publicly-known creds.
    if os.environ.get("ENVIRONMENT", "development") != "development":
        raise RuntimeError(
            "DATABASE_URL is required when ENVIRONMENT is not 'development'"
        )
    return "postgresql+psycopg://emend:emend@localhost:5432/emend"


@dataclass
class Settings:
    environment: str = field(
        default_factory=lambda: os.environ.get("ENVIRONMENT", "development")
    )
    database_url: str = field(default_factory=_resolve_database_url)
    artifacts_dir: str = field(
        default_factory=lambda: os.environ.get("ARTIFACTS_DIR", "./artifacts")
    )
    cors_origins: list[str] = field(
        default_factory=lambda: [
            o.strip()
            for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
            if o.strip()
        ]
    )
    session_cookie_name: str = "emend_session"
    session_cookie_max_age: int = 60 * 60 * 24 * 365
    # Vercel (web) and Railway (api) are cross-site in prod: set
    # SESSION_COOKIE_SAMESITE=none + SESSION_COOKIE_SECURE=1 there.
    session_cookie_secure: bool = field(
        default_factory=lambda: _env_bool("SESSION_COOKIE_SECURE", False)
    )
    session_cookie_samesite: str = field(
        default_factory=lambda: os.environ.get("SESSION_COOKIE_SAMESITE", "lax")
    )
    max_text_chars: int = field(
        default_factory=lambda: int(os.environ.get("MAX_TEXT_CHARS", "50000"))
    )
    max_body_bytes: int = field(
        default_factory=lambda: int(os.environ.get("MAX_BODY_BYTES", "2000000"))
    )


settings = Settings()
