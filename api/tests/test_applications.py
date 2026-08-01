import uuid
from pathlib import Path

import pytest

from api import core_bridge
from api.core_bridge import CoreUnavailableError
from core.schemas import (
    BulletVerdict,
    JDExtract,
    Report,
    TailoredBullet,
    TailoredResume,
    TailoredSection,
)

FAKE_TEX = """\\documentclass{article}
% grounded: ACME-01, ACME-02
\\begin{document}Sam Sample\\end{document}
"""


@pytest.fixture()
def pipeline(monkeypatch, tmp_path):
    """Stub every core/latex call at the bridge seam and record invocations."""
    calls = []

    def parse_jd(text):
        calls.append("parse_jd")
        return JDExtract(
            company="Acme Cloud",
            title="Backend Engineer",
            hard_skills=["python", "postgresql"],
            soft_requirements=["ownership"],
            responsibilities=["ship REST APIs"],
            keywords=["python", "postgresql", "kubernetes"],
        )

    def keyword_match(jd, master):
        calls.append("keyword_match")
        return 0.82, ["python", "postgresql"], ["kubernetes"]

    def tailor(master, jd):
        calls.append("tailor")
        return TailoredResume(
            summary_of_strategy="Lead with backend work",
            experiences=[
                TailoredSection(
                    ref_id="ACME",
                    bullets=[
                        TailoredBullet(
                            text="Built a reporting dashboard",
                            source_fact_ids=["ACME-01"],
                        )
                    ],
                )
            ],
            projects=[],
            skills={"Languages": ["Python"]},
        )

    def validate(master, tailored, match_score, matched_keywords, missing_keywords):
        calls.append("validate")
        return Report(
            match_score=match_score,
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
            grounding_ok=True,
            verdicts=[
                BulletVerdict(
                    bullet="Built a reporting dashboard",
                    supported=True,
                    reason="cites ACME-01",
                )
            ],
        )

    def render_and_compile(master, tailored):
        calls.append("render_and_compile")
        pdf = tmp_path / "out.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        return FAKE_TEX, str(pdf), "compile ok"

    for name, fn in [
        ("parse_jd", parse_jd),
        ("keyword_match", keyword_match),
        ("tailor", tailor),
        ("validate", validate),
        ("render_and_compile", render_and_compile),
    ]:
        monkeypatch.setattr(core_bridge, name, fn)
    return calls


def confirm_master(client, master):
    assert client.put("/resumes/master", json=master.model_dump()).status_code == 200


def test_requires_confirmed_master(client, pipeline):
    r = client.post("/applications", json={})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "no_master_resume"


def test_refactor_mode_end_to_end(client, master, pipeline):
    from api.config import settings

    confirm_master(client, master)
    r = client.post("/applications", json={})
    assert r.status_code == 202
    app_id = r.json()["id"]

    got = client.get(f"/applications/{app_id}").json()
    assert got["status"] == "done"
    assert got["mode"] == "refactor"
    assert got["match_score"] is None and got["error"] is None
    # the whole JD pipeline is skipped in refactor mode
    assert pipeline == ["render_and_compile"]

    version = got["version"]
    assert version["tex"] == FAKE_TEX  # verbatim, receipts intact
    assert "% grounded:" in version["tex"]
    assert version["report"] is None
    assert version["pdf_url"] == f"/artifacts/{version['id']}.pdf"
    assert version["tex_url"] == f"/artifacts/{version['id']}.tex"
    copied = Path(settings.artifacts_dir) / f"{version['id']}.pdf"
    assert copied.read_bytes() == b"%PDF-1.4 fake"


def test_tailor_mode_end_to_end(client, master, pipeline):
    confirm_master(client, master)
    r = client.post("/applications", json={"jd_text": "We need a backend engineer..."})
    assert r.status_code == 202
    got = client.get(f"/applications/{r.json()['id']}").json()

    assert got["status"] == "done"
    assert got["mode"] == "tailor"
    assert got["match_score"] == 0.82
    assert got["matched_keywords"] == ["python", "postgresql"]
    assert got["missing_keywords"] == ["kubernetes"]
    assert pipeline == [
        "parse_jd",
        "keyword_match",
        "tailor",
        "validate",
        "render_and_compile",
    ]

    report = got["version"]["report"]
    assert report["grounding_ok"] is True
    assert report["match_score"] == 0.82
    assert report["verdicts"][0]["supported"] is True


def test_compile_failure_surfaces_log(client, master, pipeline, monkeypatch):
    def failing_render(master_, tailored):
        return "\\documentclass{article}", "", "! LaTeX Error: something exploded"

    monkeypatch.setattr(core_bridge, "render_and_compile", failing_render)
    confirm_master(client, master)
    r = client.post("/applications", json={})
    got = client.get(f"/applications/{r.json()['id']}").json()
    assert got["status"] == "failed"
    assert got["error"] == "! LaTeX Error: something exploded"
    assert got["version"] is None


def test_unknown_fact_ids_fail_cleanly(client, master, pipeline, monkeypatch):
    def raising_render(master_, tailored):
        raise ValueError("tailored resume references unknown fact ids: {'GA-99'}")

    monkeypatch.setattr(core_bridge, "render_and_compile", raising_render)
    confirm_master(client, master)
    r = client.post("/applications", json={})
    got = client.get(f"/applications/{r.json()['id']}").json()
    assert got["status"] == "failed"
    assert "unknown fact ids" in got["error"]


def test_unexpected_error_never_leaves_running(client, master, pipeline, monkeypatch):
    def exploding_parse(text):
        raise RuntimeError("anthropic API melted")

    monkeypatch.setattr(core_bridge, "parse_jd", exploding_parse)
    confirm_master(client, master)
    r = client.post("/applications", json={"jd_text": "a posting"})
    got = client.get(f"/applications/{r.json()['id']}").json()
    assert got["status"] == "failed"
    assert "RuntimeError" in got["error"]


def test_tailor_mode_runs_real_core_pipeline_under_mock(
    client, master, monkeypatch, tmp_path
):
    """No core_bridge stubs except render_and_compile (a different
    workflow's concern, already covered by latex's own tests) -- this
    exercises the real MOCK=1 parse_jd/tailor/validate pipeline through the
    actual background job, not the `pipeline` fixture's hardcoded fakes."""

    def fake_render(master_, tailored):
        pdf = tmp_path / "out.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        return "\\documentclass{article}\n% grounded: ACME-01\n", str(pdf), "compile ok"

    monkeypatch.setattr(core_bridge, "render_and_compile", fake_render)
    confirm_master(client, master)

    r = client.post(
        "/applications",
        json={"jd_text": "Looking for a Python engineer with PostgreSQL and Docker."},
    )
    assert r.status_code == 202
    got = client.get(f"/applications/{r.json()['id']}").json()

    assert got["status"] == "done"
    assert got["mode"] == "tailor"
    assert got["match_score"] is not None
    report = got["version"]["report"]
    assert report["grounding_ok"] is True
    assert all(v["supported"] for v in report["verdicts"])
    assert all(v["source_fact_ids"] for v in report["verdicts"])


def test_run_application_rolls_back_before_marking_failed(
    client, master, pipeline, monkeypatch
):
    """A mid-run failure must clear the aborted transaction before the
    failure commit, or that commit raises too and strands status=running."""
    from api import db as db_module

    calls = []
    original_factory = db_module.SessionLocal

    def spying_factory():
        session = original_factory()
        real_rollback = session.rollback

        def spy_rollback():
            calls.append("rollback")
            real_rollback()

        session.rollback = spy_rollback
        return session

    monkeypatch.setattr(db_module, "SessionLocal", spying_factory)

    def exploding_parse(text):
        raise RuntimeError("boom")

    monkeypatch.setattr(core_bridge, "parse_jd", exploding_parse)
    confirm_master(client, master)
    r = client.post("/applications", json={"jd_text": "a posting"})
    got = client.get(f"/applications/{r.json()['id']}").json()

    assert got["status"] == "failed"
    assert calls == ["rollback"]


def test_core_unavailable_fails_the_job(client, master, pipeline, monkeypatch):
    def unavailable(text):
        raise CoreUnavailableError("core.parse_jd is not available yet")

    monkeypatch.setattr(core_bridge, "parse_jd", unavailable)
    confirm_master(client, master)
    r = client.post("/applications", json={"jd_text": "a posting"})
    got = client.get(f"/applications/{r.json()['id']}").json()
    assert got["status"] == "failed"
    assert "not available yet" in got["error"]


def test_get_is_session_scoped(client, other_client, master, pipeline):
    confirm_master(client, master)
    app_id = client.post("/applications", json={}).json()["id"]
    assert client.get(f"/applications/{app_id}").status_code == 200
    assert other_client.get(f"/applications/{app_id}").status_code == 404
    assert client.get(f"/applications/{uuid.uuid4()}").status_code == 404


def test_history_lists_own_applications_only(client, other_client, master, pipeline):
    confirm_master(client, master)
    confirm_master(other_client, master)
    a = client.post("/applications", json={}).json()["id"]
    b = client.post("/applications", json={"jd_text": "posting"}).json()["id"]
    other_client.post("/applications", json={})

    items = client.get("/applications").json()
    assert [i["id"] for i in items] == [b, a] or [i["id"] for i in items] == [a, b]
    assert len(items) == 2
    assert all(i["status"] == "done" for i in items)
    assert len(other_client.get("/applications").json()) == 1


def test_jd_text_capped(client, master, pipeline):
    from api.config import settings

    confirm_master(client, master)
    r = client.post(
        "/applications", json={"jd_text": "x" * (settings.max_text_chars + 1)}
    )
    assert r.status_code == 422
