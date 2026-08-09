from fastapi.testclient import TestClient

from api.config import settings
from api.main import create_app


def test_docs_are_served_in_development(monkeypatch):
    monkeypatch.setattr(settings, "environment", "development")
    with TestClient(create_app()) as client:
        assert client.get("/docs").status_code == 200
        assert client.get("/openapi.json").status_code == 200


def test_docs_are_disabled_outside_development(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    with TestClient(create_app()) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/redoc").status_code == 404
        assert client.get("/openapi.json").status_code == 404
