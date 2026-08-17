from pathlib import Path

import pytest

from api import core_bridge
from api.config import settings
from api.core_bridge import CoreUnavailableError
from api.tests.conftest import sample_master

PDF_FIXTURES = Path(__file__).resolve().parents[2] / "core" / "fixtures" / "pdfs"


@pytest.fixture()
def stub_structure(monkeypatch):
    def fake_structure_resume(text: str):
        return sample_master()

    monkeypatch.setattr(core_bridge, "structure_resume", fake_structure_resume)


def test_import_returns_proposed_schema_unsaved(client, stub_structure):
    r = client.post("/resumes/import", json={"text": "my resume text"})
    assert r.status_code == 200
    assert r.json()["name"] == "Sam Sample"
    assert r.json()["experiences"][0]["facts"][0]["id"] == "ACME-01"
    # nothing was saved: master is still absent
    assert client.get("/resumes/master").status_code == 404


def test_import_503_when_core_missing(client, monkeypatch):
    def unavailable(text: str):
        raise CoreUnavailableError("core.structure_resume is not available yet")

    monkeypatch.setattr(core_bridge, "structure_resume", unavailable)
    r = client.post("/resumes/import", json={"text": "hi"})
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "core_unavailable"


def test_import_text_required_and_capped(client, stub_structure):
    assert client.post("/resumes/import", json={}).status_code == 422
    assert client.post("/resumes/import", json={"text": ""}).status_code == 422
    too_long = "x" * (settings.max_text_chars + 1)
    r = client.post("/resumes/import", json={"text": too_long})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


def test_import_parses_pasted_text_via_real_core(client, monkeypatch):
    # no stubs: the real MOCK=1 pipeline must structure ordinary pasted text
    monkeypatch.setenv("MOCK", "1")
    text = "Sam Sample\nsam@example.com\n\nAcme Corp\n• Built 25+ integration tests."
    r = client.post("/resumes/import", json={"text": text})
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Sam Sample"
    assert body["experiences"][0]["company"] == "Acme Corp"
    assert body["experiences"][0]["facts"][0]["id"] == "AC-01"


def test_import_422_for_invalid_fenced_json(client, monkeypatch):
    monkeypatch.setenv("MOCK", "1")
    r = client.post("/resumes/import", json={"text": "```json\n{not valid}\n```"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "unstructurable_resume"


def test_import_accepts_multipart_pdf_upload(client, monkeypatch):
    captured = {}

    def fake_structure_resume(text: str):
        captured["text"] = text
        return sample_master()

    monkeypatch.setattr(core_bridge, "structure_resume", fake_structure_resume)

    pdf_bytes = (PDF_FIXTURES / "sample_resume.pdf").read_bytes()
    r = client.post(
        "/resumes/import",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
        headers={"X-Requested-With": "emend-web"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Sam Sample"
    # the extracted PDF text, not a placeholder, reached structure_resume
    assert "Jordan Rivera" in captured["text"]


def test_import_multipart_without_file_field_is_422(client, stub_structure):
    r = client.post(
        "/resumes/import",
        files={"not_file": ("x.txt", b"hello", "text/plain")},
        headers={"X-Requested-With": "emend-web"},
    )
    assert r.status_code == 422


def test_import_rejects_unparseable_pdf_upload(client, stub_structure):
    r = client.post(
        "/resumes/import",
        files={"file": ("resume.pdf", b"not a pdf at all", "application/pdf")},
        headers={"X-Requested-With": "emend-web"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "unstructurable_resume"


def test_import_multipart_without_csrf_header_is_rejected(client, stub_structure):
    # multipart/form-data is a CORS "simple" content type -- a cross-site
    # page could POST it with the session cookie and no preflight. The
    # required header forces a preflight, which blocks any origin outside
    # the CORS allowlist before this handler ever runs.
    pdf_bytes = (PDF_FIXTURES / "sample_resume.pdf").read_bytes()
    r = client.post(
        "/resumes/import",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "missing_csrf_header"


def test_master_round_trip_and_upsert(client, master):
    assert client.put("/resumes/master", json=master.model_dump()).status_code == 200
    got = client.get("/resumes/master")
    assert got.status_code == 200
    assert got.json() == master.model_dump()

    master.name = "Sam Updated"
    assert client.put("/resumes/master", json=master.model_dump()).status_code == 200
    assert client.get("/resumes/master").json()["name"] == "Sam Updated"


def test_master_rejects_invalid_schema(client):
    r = client.put("/resumes/master", json={"name": "no other fields"})
    assert r.status_code == 422


def test_save_master_recovers_from_concurrent_first_save(master, db_engine, monkeypatch):
    """Two near-simultaneous first-saves for the same brand-new session both
    pass save_master's "does a row already exist" check before either
    commits -- simulated here by having a second, independent DB session
    win the insert race right after this request's own `db.add`, so the
    real `db.commit()` below hits the session_id unique constraint for real."""
    from sqlalchemy.orm import sessionmaker

    from api.models import MasterResumeRow, SessionRow
    from api.routers.resumes import save_master

    Session = sessionmaker(bind=db_engine, expire_on_commit=False)
    setup = Session()
    session_row = SessionRow()
    setup.add(session_row)
    setup.commit()
    setup.close()

    db = Session()
    real_add = db.add

    def add_then_race(row):
        real_add(row)
        other = Session()
        other.add(MasterResumeRow(session_id=session_row.id, data={"raced": True}))
        other.commit()
        other.close()

    monkeypatch.setattr(db, "add", add_then_race)

    result = save_master(master, session_row, db)

    assert result == master
    check = Session()
    saved = check.query(MasterResumeRow).filter_by(session_id=session_row.id).first()
    assert saved.data["name"] == master.name  # this request's data won, not "raced"


def test_oversized_body_rejected(client):
    huge = "x" * (settings.max_body_bytes + 1)
    r = client.post(
        "/resumes/import", content=huge, headers={"content-type": "application/json"}
    )
    assert r.status_code == 413
    assert r.json()["error"]["code"] == "payload_too_large"


def test_oversized_streamed_body_rejected_with_no_content_length(client):
    # A streamed/chunked body has no Content-Length header at all -- the
    # size guard has to cap it as it arrives, not just read one header.
    def chunks():
        chunk = b"x" * 8192
        sent = 0
        while sent <= settings.max_body_bytes:
            yield chunk
            sent += len(chunk)

    r = client.post(
        "/resumes/import", content=chunks(), headers={"content-type": "application/json"}
    )
    assert r.status_code == 413
    assert r.json()["error"]["code"] == "payload_too_large"
