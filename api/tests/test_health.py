def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_health_reports_unhealthy_when_db_unreachable(client, monkeypatch):
    from api import db as db_module

    class BrokenEngine:
        def connect(self):
            raise RuntimeError("connection refused")

    monkeypatch.setattr(db_module, "engine", BrokenEngine())
    r = client.get("/health")
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "db_unreachable"


def test_unknown_route_uses_error_shape(client):
    r = client.get("/nope")
    assert r.status_code == 404
    body = r.json()
    assert body["error"]["code"] == "not_found"
    assert "message" in body["error"]
