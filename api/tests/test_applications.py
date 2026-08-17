import uuid
from pathlib import Path

from api import core_bridge
from api.core_bridge import CoreUnavailableError
from api.tests.conftest import FAKE_TEX, _fake_stream
from core.schemas import Fact, TailoredBullet, TailoredResume, TailoredSection
from core.validation import GroundingError


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


def test_run_application_cleans_up_source_render_directory(client, master, pipeline, tmp_path):
    # compile_tex() hands back a freshly minted temp dir holding just the
    # PDF; the background job copies it into artifacts_dir and must remove
    # that source dir, or every application leaks one forever.
    confirm_master(client, master)
    app_id = client.post("/applications", json={}).json()["id"]
    got = client.get(f"/applications/{app_id}").json()
    assert got["status"] == "done"
    assert not (tmp_path / "artifact").exists()


def test_polish_upgrades_a_formatted_application_end_to_end(client, master, pipeline):
    confirm_master(client, master)
    app_id = client.post("/applications", json={}).json()["id"]
    assert client.get(f"/applications/{app_id}").json()["mode"] == "refactor"

    r = client.post(f"/applications/{app_id}/polish")
    assert r.status_code == 202
    assert r.json()["mode"] == "polish"

    got = client.get(f"/applications/{app_id}").json()
    assert got["status"] == "done"
    assert got["mode"] == "polish"
    assert got["match_score"] is None and got["error"] is None
    # no JD to parse/score against, but grounding still gets a report
    assert pipeline == ["render_and_compile", "validate", "render_and_compile"]

    version = got["version"]
    assert version["report"] is not None
    assert version["report"]["grounding_ok"] is True
    assert version["tailored"] is not None


def test_polish_rejects_a_tailor_mode_application(client, master, pipeline):
    confirm_master(client, master)
    app_id = client.post("/applications", json={"jd_text": "We need a backend engineer..."}).json()[
        "id"
    ]

    r = client.post(f"/applications/{app_id}/polish")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "not_polishable"


def test_polish_rejects_someone_elses_application(client, other_client, master, pipeline):
    confirm_master(client, master)
    app_id = client.post("/applications", json={}).json()["id"]

    assert other_client.post(f"/applications/{app_id}/polish").status_code == 404


def test_polish_rejects_a_concurrently_claimed_application(db_engine, monkeypatch):
    """Two near-simultaneous polish requests both read status="done" before
    either commits -- simulated here by having a second, independent DB
    session flip status to "queued" (as if it already claimed the job)
    right before this request's own atomic UPDATE runs, so that UPDATE's
    WHERE clause really does see the raced state and affects zero rows."""
    import pytest
    from fastapi import BackgroundTasks
    from sqlalchemy import update
    from sqlalchemy.orm import sessionmaker

    from api.errors import ApiError
    from api.models import Application, SessionRow
    from api.routers.applications import polish_application

    Session = sessionmaker(bind=db_engine, expire_on_commit=False)
    setup = Session()
    session_row = SessionRow()
    setup.add(session_row)
    setup.flush()
    app_row = Application(session_id=session_row.id, mode="refactor", status="done")
    setup.add(app_row)
    setup.commit()
    app_id = app_row.id
    setup.close()

    db = Session()
    real_execute = db.execute

    def execute_then_race(statement, *args, **kwargs):
        if getattr(statement, "is_update", False):
            other = Session()
            claim = update(Application).where(Application.id == app_id).values(status="queued")
            other.execute(claim)
            other.commit()
            other.close()
        return real_execute(statement, *args, **kwargs)

    monkeypatch.setattr(db, "execute", execute_then_race)

    fresh_session_row = db.get(SessionRow, session_row.id)
    with pytest.raises(ApiError) as exc_info:
        polish_application(app_id, fresh_session_row, db, BackgroundTasks())
    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "already_running"


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
        artifact_dir = tmp_path / "artifact"
        artifact_dir.mkdir(exist_ok=True)
        pdf = artifact_dir / "out.pdf"
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
    monkeypatch.setattr(
        core_bridge.httpx,
        "stream",
        _fake_stream(
            "<html><body><nav>skip me</nav>"
            "<main>We need a backend engineer with Python.</main></body></html>"
        ),
    )

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

    def failing_stream(*a, **k):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(core_bridge.httpx, "stream", failing_stream)
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


def test_preview_reorders_sections_via_section_order(client, master, pipeline):
    confirm_master(client, master)
    app_id = client.post("/applications", json={}).json()["id"]

    reordered = client.post(
        f"/applications/{app_id}/preview",
        json={"section_order": ["PROJECTS", "EXPERIENCE", "EDUCATION", "SKILLS"]},
    )
    tex = reordered.json()["tex"]
    assert tex.index(r"\section{Projects}") < tex.index(r"\section{Experience}")
    assert tex.index(r"\section{Experience}") < tex.index(r"\section{Education}")


def test_preview_deletes_a_bullet_via_excluded_facts(client, master, pipeline):
    confirm_master(client, master)
    app_id = client.post("/applications", json={}).json()["id"]

    default = client.post(f"/applications/{app_id}/preview", json={})
    assert "Built an internal reporting dashboard" in default.json()["tex"]

    deleted = client.post(
        f"/applications/{app_id}/preview",
        json={"excluded_facts": ["ACME-01"]},
    )
    assert "Built an internal reporting dashboard" not in deleted.json()["tex"]


def test_preview_deletes_a_whole_entry_via_excluded_experiences(client, master, pipeline):
    confirm_master(client, master)
    app_id = client.post("/applications", json={}).json()["id"]

    deleted = client.post(
        f"/applications/{app_id}/preview",
        json={"excluded_experiences": ["ACME"]},
    )
    tex = deleted.json()["tex"]
    assert "Acme Corp" not in tex
    assert r"\section{Experience}" not in tex


def test_preview_applies_text_overrides(client, master, pipeline):
    confirm_master(client, master)
    app_id = client.post("/applications", json={}).json()["id"]

    edited = client.post(
        f"/applications/{app_id}/preview",
        json={
            "text_overrides": {
                "name": "Sam T. Sample",
                "experience:ACME:company": "Renamed Corp",
                "skills:Languages": "Python, Rust",
            }
        },
    )
    tex = edited.json()["tex"]
    assert "Sam T. Sample" in tex
    assert "Renamed Corp" in tex
    assert "Python, Rust" in tex
    assert "Acme Corp" not in tex


def test_finalize_is_race_free_under_concurrent_calls(db_engine, master, tmp_path, monkeypatch):
    """Two near-simultaneous finalize calls for the same application must not
    interleave one request's PDF write with another's DB commit -- otherwise
    the stored version.tex and the PDF actually on disk can come from two
    different compiles, and a user downloads a PDF that silently doesn't
    match the .tex shown for that version."""
    import threading
    import time as time_module

    from sqlalchemy.orm import sessionmaker

    from api import core_bridge
    from api.models import Application, MasterResumeRow, ResumeVersion, SessionRow
    from api.routers.applications import finalize_application
    from api.schemas import RenderRequest

    Session = sessionmaker(bind=db_engine, expire_on_commit=False)
    setup = Session()
    session_row = SessionRow()
    setup.add(session_row)
    setup.flush()
    setup.add(MasterResumeRow(session_id=session_row.id, data=master.model_dump()))
    app_row = Application(session_id=session_row.id, mode="refactor", status="done")
    setup.add(app_row)
    setup.flush()
    setup.add(ResumeVersion(application_id=app_row.id, tex="orig", pdf_path=""))
    setup.commit()
    app_id = app_row.id
    setup.close()

    calls = {"n": 0}
    calls_lock = threading.Lock()

    def fake_render_and_compile(master_, tailored, **kwargs):
        with calls_lock:
            n = calls["n"]
            calls["n"] += 1
        # widen the window between compile and this call's own file
        # write+commit, so an unlocked handler reliably interleaves with a
        # concurrent call instead of rarely colliding.
        time_module.sleep(0.02)
        artifact_dir = tmp_path / f"artifact-{n}"
        artifact_dir.mkdir()
        pdf = artifact_dir / "out.pdf"
        pdf.write_bytes(f"%PDF marker-{n}".encode())
        return f"tex-marker-{n}", str(pdf), "compile ok"

    monkeypatch.setattr(core_bridge, "render_and_compile", fake_render_and_compile)

    results = []
    results_lock = threading.Lock()

    def attempt():
        db = Session()
        try:
            session_local = db.get(SessionRow, session_row.id)
            out = finalize_application(app_id, RenderRequest(), session_local, db)
            with results_lock:
                results.append(out)
        finally:
            db.close()

    threads = [threading.Thread(target=attempt) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    check = Session()
    final_version = check.get(ResumeVersion, results[0].id)
    tex_marker = final_version.tex.removeprefix("tex-marker-")
    pdf_bytes = pathlib_read(final_version.pdf_path)
    assert pdf_bytes == f"%PDF marker-{tex_marker}".encode()


def pathlib_read(path: str) -> bytes:
    from pathlib import Path

    return Path(path).read_bytes()


def test_finalize_recompiles_and_updates_the_version(client, master, pipeline):
    confirm_master(client, master)
    app_id = client.post("/applications", json={"jd_text": "a posting"}).json()["id"]

    r = client.post(f"/applications/{app_id}/finalize", json={})
    assert r.status_code == 200
    assert r.json()["tex"] == FAKE_TEX


def test_finalize_cleans_up_source_render_directory(client, master, pipeline, tmp_path):
    confirm_master(client, master)
    app_id = client.post("/applications", json={"jd_text": "a posting"}).json()["id"]

    r = client.post(f"/applications/{app_id}/finalize", json={})
    assert r.status_code == 200
    assert not (tmp_path / "artifact").exists()


def test_finalize_is_rate_limited(client, master, pipeline):
    # finalize triggers a real LaTeX compile -- it must be capped like
    # create/polish are, not left wide open
    confirm_master(client, master)
    app_id = client.post("/applications", json={"jd_text": "a posting"}).json()["id"]

    for _ in range(30):
        assert client.post(f"/applications/{app_id}/finalize", json={}).status_code == 200
    r = client.post(f"/applications/{app_id}/finalize", json={})
    assert r.status_code == 429


def test_preview_is_rate_limited(client, master, pipeline):
    confirm_master(client, master)
    app_id = client.post("/applications", json={"jd_text": "a posting"}).json()["id"]

    for _ in range(300):
        assert client.post(f"/applications/{app_id}/preview", json={}).status_code == 200
    r = client.post(f"/applications/{app_id}/preview", json={})
    assert r.status_code == 429


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


def test_preview_applies_every_edit_kind_at_once_refactor_mode(client, master, pipeline):
    """The full "edit every line on Just Typeset It" path: header, education,
    experience/project structural fields, skills, a section rename, a
    reorder, and a delete, all in one request -- proving none of these
    features step on each other when combined, the way a real editing
    session actually would."""
    confirm_master(client, master)
    app_id = client.post("/applications", json={}).json()["id"]

    body = {
        "fact_order": {"ACME": ["ACME-02", "ACME-01"]},
        "excluded_facts": ["PROJ-01"],
        "text_overrides": {
            "name": "Samantha T. Sample",
            "email": "samantha@newmail.com",
            "phone": "555-9999",
            "link:0": "linkedin.com/in/samantha",
            "education:0:school": "Sample State University (Honors)",
            "education:0:degree": "B.S. in Computer Science",
            "education:0:coursework": "Distributed Systems, Compilers",
            "experience:ACME:title": "Senior Software Engineering Intern",
            "experience:ACME:company": "Acme Corporation",
            "experience:ACME:start": "May 2025",
            "project:PROJ:name": "Course Scheduler 2.0",
            "project:PROJ:tech": "Rust, SQLite",
            "skills:Languages": "Python, SQL, Rust",
            "section:EXPERIENCE:heading": "Leadership",
        },
    }
    r = client.post(f"/applications/{app_id}/preview", json=body)
    assert r.status_code == 200
    tex = r.json()["tex"]

    # header
    assert "Samantha T. Sample" in tex
    assert "samantha@newmail.com" in tex
    assert "555-9999" in tex
    assert "samantha" in tex
    # education
    assert "Sample State University (Honors)" in tex
    assert "B.S. in Computer Science" in tex
    assert "Distributed Systems, Compilers" in tex
    # experience structural fields + renamed section heading
    assert "Senior Software Engineering Intern" in tex
    assert "Acme Corporation" in tex
    assert "May 2025" in tex
    assert r"\section{Leadership}" in tex
    assert r"\section{Experience}" not in tex
    # project structural fields
    assert "Course Scheduler 2.0" in tex
    assert "Rust, SQLite" in tex
    # skills
    assert r"\textbf{Languages}{: Python, SQL, Rust}" in tex
    # reorder: ACME-02's bullet before ACME-01's
    assert tex.index("Wrote integration tests") < tex.index("Built an internal reporting")
    # delete: PROJ's only bullet is gone but the project entry itself remains
    assert "Constraint solver for course timetables" not in tex
    assert "Course Scheduler 2.0" in tex


def test_preview_applies_every_edit_kind_at_once_tailor_mode(
    client, master, pipeline, monkeypatch
):
    """Same combined-edit proof as the refactor-mode version above, but for
    an actual tailored (job-posting-matched) resume -- editing must work
    identically whether or not a real tailor pass produced the bullets."""

    def tailor(master_, jd):
        return TailoredResume(
            summary_of_strategy="x",
            experiences=[
                TailoredSection(
                    ref_id="ACME",
                    bullets=[
                        TailoredBullet(
                            variants=["Built the dashboard"] * 3,
                            source_fact_ids=["ACME-01"],
                        ),
                        TailoredBullet(
                            variants=["Wrote the tests"] * 3,
                            source_fact_ids=["ACME-02"],
                        ),
                    ],
                )
            ],
            projects=[
                TailoredSection(
                    ref_id="PROJ",
                    bullets=[
                        TailoredBullet(
                            variants=["Solved scheduling"] * 3,
                            source_fact_ids=["PROJ-01"],
                        ),
                    ],
                )
            ],
            skills={"Languages": ["Python", "SQL"]},
        )

    monkeypatch.setattr(core_bridge, "tailor", tailor)
    confirm_master(client, master)
    app_id = client.post("/applications", json={"jd_text": "a posting"}).json()["id"]

    body = {
        "fact_order": {"ACME": ["ACME-02", "ACME-01"]},
        "excluded_facts": ["PROJ-01"],
        "text_overrides": {
            "name": "Samantha T. Sample",
            "experience:ACME:title": "Senior Software Engineering Intern",
            "project:PROJ:name": "Course Scheduler 2.0",
            "skills:Languages": "Python, SQL, Rust",
            "section:PROJECTS:heading": "Side Projects",
        },
    }
    r = client.post(f"/applications/{app_id}/preview", json=body)
    assert r.status_code == 200
    tex = r.json()["tex"]

    assert "Samantha T. Sample" in tex
    assert "Senior Software Engineering Intern" in tex
    assert "Course Scheduler 2.0" in tex
    assert r"\textbf{Languages}{: Python, SQL, Rust}" in tex
    assert r"\section{Side Projects}" in tex
    assert tex.index("Wrote the tests") < tex.index("Built the dashboard")
    assert "Solved scheduling" not in tex
    assert "Course Scheduler 2.0" in tex


def test_jd_text_capped(client, master, pipeline):
    from api.config import settings

    confirm_master(client, master)
    r = client.post(
        "/applications", json={"jd_text": "x" * (settings.max_text_chars + 1)}
    )
    assert r.status_code == 422


def test_preview_text_override_value_is_capped(client, master, pipeline):
    from api.config import settings

    confirm_master(client, master)
    app_id = client.post("/applications", json={"jd_text": "a posting"}).json()["id"]

    r = client.post(
        f"/applications/{app_id}/preview",
        json={"text_overrides": {"name": "x" * (settings.max_text_chars + 1)}},
    )
    assert r.status_code == 422


def test_preview_custom_bullet_text_is_capped(client, master, pipeline):
    from api.config import settings

    confirm_master(client, master)
    app_id = client.post("/applications", json={"jd_text": "a posting"}).json()["id"]

    r = client.post(
        f"/applications/{app_id}/preview",
        json={"selections": {"ACME-01": {"custom_text": "x" * (settings.max_text_chars + 1)}}},
    )
    assert r.status_code == 422
