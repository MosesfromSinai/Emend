from fastapi.testclient import TestClient

from api.config import settings
from api.main import create_app


def test_docs_are_served_in_development(db_engine, monkeypatch):
    # db_engine swaps in a real (SQLite) engine -- app startup now reaps
    # stuck applications, which needs a working DB to connect to.
    monkeypatch.setattr(settings, "environment", "development")
    with TestClient(create_app()) as client:
        assert client.get("/docs").status_code == 200
        assert client.get("/openapi.json").status_code == 200


def test_docs_are_disabled_outside_development(db_engine, monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    with TestClient(create_app()) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/redoc").status_code == 404
        assert client.get("/openapi.json").status_code == 404
