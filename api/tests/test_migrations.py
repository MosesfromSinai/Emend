"""Migrations must reproduce the schema from zero (acceptance criterion)."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

API_DIR = Path(__file__).resolve().parents[1]

EXPECTED_TABLES = {"sessions", "master_resumes", "applications", "resume_versions"}


def test_upgrade_from_zero_and_downgrade(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path}/migrate.db"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = Config(str(API_DIR / "alembic.ini"))

    command.upgrade(cfg, "head")
    engine = create_engine(url)
    tables = set(inspect(engine).get_table_names())
    assert EXPECTED_TABLES <= tables

    app_cols = {c["name"] for c in inspect(engine).get_columns("applications")}
    assert {
        "id",
        "session_id",
        "mode",
        "jd_text",
        "status",
        "match_score",
        "matched_keywords",
        "missing_keywords",
        "error",
        "created_at",
    } <= app_cols
    engine.dispose()

    command.downgrade(cfg, "base")
    engine = create_engine(url)
    assert not EXPECTED_TABLES & set(inspect(engine).get_table_names())
    engine.dispose()


def test_migration_matches_models(tmp_path, monkeypatch):
    """The migration and Base.metadata must describe the same tables."""
    from api.db import Base

    url = f"sqlite:///{tmp_path}/parity.db"
    monkeypatch.setenv("DATABASE_URL", url)
    command.upgrade(Config(str(API_DIR / "alembic.ini")), "head")
    engine = create_engine(url)
    insp = inspect(engine)
    for table_name, table in Base.metadata.tables.items():
        migrated = {c["name"] for c in insp.get_columns(table_name)}
        modeled = {c.name for c in table.columns}
        assert migrated == modeled, f"{table_name}: {migrated ^ modeled}"
    engine.dispose()
