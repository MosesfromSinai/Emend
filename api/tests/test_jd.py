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


def test_url_fetch_sends_a_browser_user_agent(client, master, monkeypatch):
    # bot-protection CDNs in front of major careers sites (confirmed against
    # a real posting) silently hang/drop requests with no browser-like UA
    confirm_master(client, master)
    _stub_parse_and_match(monkeypatch)
    seen_headers = {}

    class FakeResponse:
        text = "<html><body><main>Role.</main></body></html>"

        def raise_for_status(self):
            pass

    def fake_get(url, **kwargs):
        seen_headers.update(kwargs.get("headers") or {})
        return FakeResponse()

    monkeypatch.setattr(core_bridge.httpx, "get", fake_get)

    client.post("/jd/preview", json={"jd_url": "https://example.com/job"})

    assert "Mozilla" in seen_headers.get("User-Agent", "")


def test_preview_rejects_both_sources(client, master):
    confirm_master(client, master)
    r = client.post(
        "/jd/preview", json={"jd_text": "a posting", "jd_url": "https://example.com/job"}
    )
    assert r.status_code == 422


def test_preview_fails_clearly_on_unreadable_url(client, master, monkeypatch):
    # a JS-rendered posting page whose fetch "succeeds" but yields no real
    # text (e.g. a React SPA shell with no JobPosting JSON-LD) must not
    # silently score as a fake 0% match
    confirm_master(client, master)

    class FakeResponse:
        text = "<html><body><noscript>Enable JavaScript to view this page.</noscript></body></html>"

        def raise_for_status(self):
            pass

    monkeypatch.setattr(core_bridge.httpx, "get", lambda *a, **k: FakeResponse())

    r = client.post("/jd/preview", json={"jd_url": "https://example.com/job"})

    assert r.status_code == 422
    assert r.json()["error"]["code"] == "jd_unscoreable"
