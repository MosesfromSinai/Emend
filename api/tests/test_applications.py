import uuid
from pathlib import Path

import pytest

from api import core_bridge
from api.core_bridge import CoreUnavailableError
from core.schemas import (
    BulletVerdict,
    Fact,
    JDExtract,
    Report,
    TailoredBullet,
    TailoredResume,
    TailoredSection,
)
from core.validation import GroundingError

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
                            variants=["Built a reporting dashboard"] * 3,
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

    def render_and_compile(master, tailored, *_args, **_kwargs):
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

    # refactor mode still wraps confirmed facts as a TailoredResume (3
    # identical variants each) so Export's per-line edit controls work here
    # too -- editing isn't gated behind having pasted a job posting.
    assert version["tailored"] is not None
    bullet = version["tailored"]["experiences"][0]["bullets"][0]
    assert bullet["source_fact_ids"] == ["ACME-01"]
    assert len(bullet["variants"]) == 3
    assert bullet["variants"][0] == bullet["variants"][1] == bullet["variants"][2]


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


def test_grounding_error_surfaces_a_friendly_message(client, master, pipeline, monkeypatch):
    # an exhausted retry loop shouldn't dump a raw "GroundingError: judge
    # rejected bullet ..." exception string at the user
    def raising_tailor(master_, jd):
        raise GroundingError('judge rejected bullet "...": overstates scope')

    monkeypatch.setattr(core_bridge, "tailor", raising_tailor)
    confirm_master(client, master)
    r = client.post("/applications", json={"jd_text": "a posting"})
    got = client.get(f"/applications/{r.json()['id']}").json()
    assert got["status"] == "failed"
    assert "GroundingError" not in got["error"]
    assert "try tailoring again" in got["error"]


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


def test_jd_url_mode_fetches_and_extracts(client, master, pipeline, monkeypatch):
    class FakeResponse:
        text = (
            "<html><body><nav>skip me</nav>"
            "<main>We need a backend engineer with Python.</main></body></html>"
        )

        def raise_for_status(self):
            pass

    monkeypatch.setattr(core_bridge.httpx, "get", lambda *a, **k: FakeResponse())

    confirm_master(client, master)
    r = client.post("/applications", json={"jd_url": "https://example.com/job"})
    assert r.status_code == 202
    got = client.get(f"/applications/{r.json()['id']}").json()

    assert got["status"] == "done"
    assert got["mode"] == "tailor"
    assert got["jd_source_url"] == "https://example.com/job"
    assert pipeline[0] == "parse_jd"


def test_jd_url_fetch_failure_fails_the_job(client, master, pipeline, monkeypatch):
    import httpx

    def failing_get(*a, **k):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(core_bridge.httpx, "get", failing_get)
    confirm_master(client, master)
    r = client.post("/applications", json={"jd_url": "https://example.com/job"})
    got = client.get(f"/applications/{r.json()['id']}").json()

    assert got["status"] == "failed"
    assert "Could not fetch job posting URL" in got["error"]
    assert pipeline == []


def test_jd_text_and_jd_url_together_is_422(client, master, pipeline):
    confirm_master(client, master)
    r = client.post(
        "/applications", json={"jd_text": "a posting", "jd_url": "https://example.com/job"}
    )
    assert r.status_code == 422


def test_preview_renders_the_selected_variant(client, master, pipeline, monkeypatch):
    def tailor(master_, jd):
        return TailoredResume(
            summary_of_strategy="x",
            experiences=[
                TailoredSection(
                    ref_id="ACME",
                    bullets=[
                        TailoredBullet(
                            variants=["first phrasing", "second phrasing", "third phrasing"],
                            source_fact_ids=["ACME-01"],
                        )
                    ],
                )
            ],
            projects=[],
            skills={},
        )

    monkeypatch.setattr(core_bridge, "tailor", tailor)
    confirm_master(client, master)
    app_id = client.post("/applications", json={"jd_text": "a posting"}).json()["id"]

    default = client.post(f"/applications/{app_id}/preview", json={})
    assert "first phrasing" in default.json()["tex"]

    picked = client.post(
        f"/applications/{app_id}/preview",
        json={"selections": {"ACME-01": {"variant_idx": 2}}},
    )
    assert "third phrasing" in picked.json()["tex"]
    assert "first phrasing" not in picked.json()["tex"]


def test_preview_reorders_bullets_via_fact_order(client, master, pipeline, monkeypatch):
    def tailor(master_, jd):
        return TailoredResume(
            summary_of_strategy="x",
            experiences=[
                TailoredSection(
                    ref_id="ACME",
                    bullets=[
                        TailoredBullet(variants=["bullet one"] * 3, source_fact_ids=["ACME-01"]),
                        TailoredBullet(variants=["bullet two"] * 3, source_fact_ids=["ACME-02"]),
                    ],
                )
            ],
            projects=[],
            skills={},
        )

    monkeypatch.setattr(core_bridge, "tailor", tailor)
    confirm_master(client, master)
    app_id = client.post("/applications", json={"jd_text": "a posting"}).json()["id"]

    default = client.post(f"/applications/{app_id}/preview", json={})
    tex = default.json()["tex"]
    assert tex.index("bullet one") < tex.index("bullet two")

    reordered = client.post(
        f"/applications/{app_id}/preview",
        json={"fact_order": {"ACME": ["ACME-02", "ACME-01"]}},
    )
    tex = reordered.json()["tex"]
    assert tex.index("bullet two") < tex.index("bullet one")


def test_preview_reorders_entries_via_experience_order(client, master, pipeline, monkeypatch):
    def tailor(master_, jd):
        return TailoredResume(
            summary_of_strategy="x",
            experiences=[
                TailoredSection(
                    ref_id="ACME",
                    bullets=[TailoredBullet(variants=["a"] * 3, source_fact_ids=["ACME-01"])],
                ),
                TailoredSection(
                    ref_id="GLOBEX",
                    bullets=[TailoredBullet(variants=["b"] * 3, source_fact_ids=["GLOBEX-01"])],
                ),
            ],
            projects=[],
            skills={},
        )

    monkeypatch.setattr(core_bridge, "tailor", tailor)
    second_experience = master.experiences[0].model_copy(
        update={
            "id": "GLOBEX",
            "company": "Globex Corp",
            "facts": [Fact(id="GLOBEX-01", text="Migrated the reporting pipeline")],
        }
    )
    two_experiences = master.model_copy(
        update={"experiences": master.experiences + [second_experience]}
    )
    confirm_master(client, two_experiences)
    app_id = client.post("/applications", json={"jd_text": "a posting"}).json()["id"]

    reordered = client.post(
        f"/applications/{app_id}/preview",
        json={"experience_order": ["GLOBEX", "ACME"]},
    )
    tex = reordered.json()["tex"]
    assert tex.index("Globex") < tex.index("Acme")


def test_finalize_recompiles_and_updates_the_version(client, master, pipeline):
    confirm_master(client, master)
    app_id = client.post("/applications", json={"jd_text": "a posting"}).json()["id"]

    r = client.post(f"/applications/{app_id}/finalize", json={})
    assert r.status_code == 200
    assert r.json()["tex"] == FAKE_TEX


def test_preview_fails_cleanly_when_master_no_longer_matches(
    client, master, pipeline, monkeypatch
):
    # editing the master resume after a tailored version cites its section
    # ids must surface a clean 409, not an unhandled ValueError -> 500
    def tailor(master_, jd):
        return TailoredResume(
            summary_of_strategy="x",
            experiences=[
                TailoredSection(
                    ref_id="ACME",
                    bullets=[
                        TailoredBullet(variants=["a", "a", "a"], source_fact_ids=["ACME-01"])
                    ],
                )
            ],
            projects=[],
            skills={},
        )

    monkeypatch.setattr(core_bridge, "tailor", tailor)
    confirm_master(client, master)
    app_id = client.post("/applications", json={"jd_text": "a posting"}).json()["id"]

    edited = master.model_copy(update={"experiences": []})
    confirm_master(client, edited)

    r = client.post(f"/applications/{app_id}/preview", json={})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "stale_tailored_resume"

    def raising_render_and_compile(master_, tailored, *_args, **_kwargs):
        raise ValueError("tailored experience section references unknown id: ACME")

    monkeypatch.setattr(core_bridge, "render_and_compile", raising_render_and_compile)
    r = client.post(f"/applications/{app_id}/finalize", json={})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "stale_tailored_resume"


def test_version_freezes_source_facts_at_generation_time(client, master, pipeline):
    """A version's fact-id -> text snapshot must survive later edits to the
    master resume, since tailored bullets cite fact ids assigned positionally
    at generation time (core.pipeline._assign_ids) that are not stable across
    edits. Regression for the "view my original" mislabeling bug: without a
    frozen snapshot, re-importing/reordering the master can make an old
    version's cited fact id resolve to the wrong fact (or none), so the UI
    falls back to showing an AI rewrite labeled as the user's original wording.
    """
    confirm_master(client, master)
    app_id = client.post("/applications", json={"jd_text": "a posting"}).json()["id"]
    version = client.get(f"/applications/{app_id}").json()["version"]

    # the tailor stub cites ACME-01, whose original text is captured here
    assert version["source_facts"]["ACME-01"] == "Built an internal reporting dashboard"

    # the user goes back and edits their master resume: ACME-01 now points at
    # completely different wording (e.g. facts were reordered on re-import)
    edited = master.model_copy(deep=True)
    edited.experiences[0].facts[0].text = "Refactored the payments pipeline"
    assert client.put("/resumes/master", json=edited.model_dump()).status_code == 200

    # the old application's snapshot must be untouched by that edit
    refetched = client.get(f"/applications/{app_id}").json()["version"]
    assert refetched["source_facts"]["ACME-01"] == "Built an internal reporting dashboard"


def test_jd_text_capped(client, master, pipeline):
    from api.config import settings

    confirm_master(client, master)
    r = client.post(
        "/applications", json={"jd_text": "x" * (settings.max_text_chars + 1)}
    )
    assert r.status_code == 422
