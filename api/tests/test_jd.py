from api import core_bridge
from core.schemas import JDExtract


def confirm_master(client, master):
    assert client.put("/resumes/master", json=master.model_dump()).status_code == 200


def _stub_parse_and_match(monkeypatch):
    def parse_jd(text):
        return JDExtract(
            company="Acme Cloud",
            title="Backend Engineer",
            hard_skills=["python"],
            soft_requirements=[],
            responsibilities=[],
            keywords=["python", "kubernetes"],
        )

    def keyword_match(jd, master):
        return 0.6, ["python"], ["kubernetes"]

    monkeypatch.setattr(core_bridge, "parse_jd", parse_jd)
    monkeypatch.setattr(core_bridge, "keyword_match", keyword_match)


def test_preview_scores_pasted_text(client, master, monkeypatch):
    confirm_master(client, master)
    _stub_parse_and_match(monkeypatch)

    r = client.post("/jd/preview", json={"jd_text": "We need a Python backend engineer."})

    assert r.status_code == 200
    body = r.json()
    assert body["score"] == 0.6
    assert body["matched_keywords"] == ["python"]
    assert body["missing_keywords"] == ["kubernetes"]
    assert body["resolved_jd_text"] == "We need a Python backend engineer."


def test_preview_scores_a_url(client, master, monkeypatch):
    confirm_master(client, master)
    _stub_parse_and_match(monkeypatch)

    class FakeResponse:
        text = "<html><body><main>Python backend role.</main></body></html>"

        def raise_for_status(self):
            pass

    monkeypatch.setattr(core_bridge.httpx, "get", lambda *a, **k: FakeResponse())

    r = client.post("/jd/preview", json={"jd_url": "https://example.com/job"})

    assert r.status_code == 200
    assert r.json()["resolved_jd_text"] == "Python backend role."


def test_preview_rejects_both_sources(client, master):
    confirm_master(client, master)
    r = client.post(
        "/jd/preview", json={"jd_text": "a posting", "jd_url": "https://example.com/job"}
    )
    assert r.status_code == 422
