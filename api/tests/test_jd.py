import pytest

from api import core_bridge
from api.core_bridge import JD_FETCH_MAX_BYTES, JdUrlBlockedError
from api.tests.conftest import _fake_stream, _FakeStreamResponse
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

    monkeypatch.setattr(
        core_bridge.httpx,
        "stream",
        _fake_stream("<html><body><main>Python backend role.</main></body></html>"),
    )

    r = client.post("/jd/preview", json={"jd_url": "https://example.com/job"})

    assert r.status_code == 200
    assert r.json()["resolved_jd_text"] == "Python backend role."


def test_url_fetch_sends_a_browser_user_agent(client, master, monkeypatch):
    # bot-protection CDNs in front of major careers sites (confirmed against
    # a real posting) silently hang/drop requests with no browser-like UA
    confirm_master(client, master)
    _stub_parse_and_match(monkeypatch)
    seen_headers = {}

    def fake_stream(method, url, **kwargs):
        seen_headers.update(kwargs.get("headers") or {})
        return _FakeStreamResponse("<html><body><main>Role.</main></body></html>")

    monkeypatch.setattr(core_bridge.httpx, "stream", fake_stream)

    client.post("/jd/preview", json={"jd_url": "https://example.com/job"})

    assert "Mozilla" in seen_headers.get("User-Agent", "")


def test_preview_rejects_a_link_pasted_into_the_text_field(client, master):
    # the Tailor screen's link field fetches a URL; pasting the same URL
    # into the text field instead must fail clearly, not silently score 0%
    confirm_master(client, master)

    r = client.post(
        "/jd/preview",
        json={"jd_text": "https://careers.roblox.com/jobs/8080438?gh_jid=8080438"},
    )

    assert r.status_code == 422
    assert r.json()["error"]["code"] == "jd_unscoreable"


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

    monkeypatch.setattr(
        core_bridge.httpx,
        "stream",
        _fake_stream(
            "<html><body><noscript>Enable JavaScript to view this page.</noscript></body></html>"
        ),
    )

    r = client.post("/jd/preview", json={"jd_url": "https://example.com/job"})

    assert r.status_code == 422
    assert r.json()["error"]["code"] == "jd_unscoreable"


def test_fetch_jd_text_aborts_when_response_exceeds_max_bytes(monkeypatch):
    # SSRF-safe doesn't bound response size -- Emend runs as a single API
    # instance, so one huge response fully buffered into memory can OOM the
    # whole process. This must abort mid-stream, not just reject a response
    # it already finished downloading.
    chunks_yielded = {"n": 0}

    class OversizedResponse:
        is_redirect = False
        encoding = "utf-8"

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def raise_for_status(self):
            pass

        def iter_bytes(self):
            chunk = b"x" * 1024
            for _ in range(1_000_000):  # far more than fits under the cap
                chunks_yielded["n"] += 1
                yield chunk

    monkeypatch.setattr(
        core_bridge.httpx, "stream", lambda method, url, **kwargs: OversizedResponse()
    )

    with pytest.raises(JdUrlBlockedError, match="exceeds"):
        core_bridge.fetch_jd_text("https://example.com/job")

    # aborted well short of consuming all 1,000,000 chunks -- proves the
    # cap stops the download, not just the final result
    assert chunks_yielded["n"] < (JD_FETCH_MAX_BYTES // 1024) + 10
